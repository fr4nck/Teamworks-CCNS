from __future__ import annotations

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QDialog, QMessageBox

from application.services.presence_write import (
    PresenceCreateCommand,
    PresenceDeleteCommand,
    PresenceTarget,
    PresenceUpdateCommand,
    create_presences,
    delete_presence,
    update_presence,
)
from application.services.service_result import ServiceErrorCode
from presence_editor import PresenceEditorDialog


class PresenceCrudController(QObject):
    """Raccord Qt fin vers le service Présences, sans SQL dans l'UI."""

    status_message = Signal(str)

    def __init__(
        self,
        page,
        *,
        read_adapter,
        write_port_factory=None,
        refresh_callback=None,
        dialog_factory=PresenceEditorDialog,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._page = page
        self._read_adapter = read_adapter
        self._write_port_factory = write_port_factory
        self._refresh_callback = refresh_callback
        self._dialog_factory = dialog_factory
        self._person_id = None
        page.action_requested.connect(self._on_action)
        self._sync_enabled()

    def set_person_id(self, person_id) -> None:
        if (
            isinstance(person_id, int)
            and not isinstance(person_id, bool)
            and person_id > 0
        ):
            self._person_id = person_id
        else:
            self._person_id = None
        self._sync_enabled()

    def _sync_enabled(self) -> None:
        self._page.set_write_enabled(
            self._person_id is not None and callable(self._write_port_factory)
        )

    def _categories(self):
        return tuple(self._read_adapter.list_presence_categories())

    def _port(self):
        if not callable(self._write_port_factory):
            raise RuntimeError("Écriture des présences indisponible.")
        return self._write_port_factory()

    def _on_action(self, action_id: str, payload) -> None:
        if self._person_id is None:
            return
        try:
            if action_id == "add":
                self._add()
            elif action_id == "edit" and payload is not None:
                self._edit(payload)
            elif action_id == "delete" and payload is not None:
                self._delete(payload)
        except Exception as exc:
            QMessageBox.critical(
                self._page,
                "Présences",
                "Opération impossible : %s" % exc,
            )

    def _add(self) -> None:
        categories = self._categories()
        if not categories:
            QMessageBox.warning(
                self._page,
                "Présences",
                "Aucune catégorie de présence n'est disponible.",
            )
            return

        dialog = self._dialog_factory(
            categories,
            person_id=self._person_id,
            parent=self._page.window(),
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        presence_date, start, end, category_id, title = dialog.values()
        result = create_presences(
            self._port(),
            command=PresenceCreateCommand(
                targets=(PresenceTarget(self._person_id, presence_date),),
                start_time=start,
                end_time=end,
                category_id=category_id,
                title=title,
            ),
        )
        self._handle_result(result, "Présence ajoutée.")

    def _edit(self, payload) -> None:
        presence_id = int(payload.key)
        port = self._port()
        snapshot = port.read_presence(presence_id)
        if snapshot is None:
            QMessageBox.warning(
                self._page,
                "Présences",
                "La présence sélectionnée n'existe plus.",
            )
            self._refresh()
            return

        categories = self._categories()
        dialog = self._dialog_factory(
            categories,
            person_id=self._person_id,
            snapshot=snapshot,
            parent=self._page.window(),
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        _presence_date, start, end, category_id, title = dialog.values()
        result = update_presence(
            port,
            command=PresenceUpdateCommand(
                presence_id=presence_id,
                start_time=start,
                end_time=end,
                category_id=category_id,
                title=title,
            ),
        )
        self._handle_result(result, "Présence modifiée.")

    def _delete(self, payload) -> None:
        presence_id = int(payload.key)
        answer = QMessageBox.question(
            self._page,
            "Supprimer la présence",
            "Supprimer définitivement la présence sélectionnée ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        result = delete_presence(
            self._port(),
            command=PresenceDeleteCommand(
                presence_id=presence_id,
                confirmed=True,
            ),
        )
        self._handle_result(result, "Présence supprimée.")

    def _handle_result(self, result, success_message: str) -> None:
        if result.ok:
            self._refresh()
            self.status_message.emit(success_message)
            return

        error = result.error
        message = error.message if error is not None else "Opération impossible."

        if (
            error is not None
            and error.code is ServiceErrorCode.READBACK_ERROR
            and result.committed
        ):
            QMessageBox.warning(
                self._page,
                "Présences",
                message + "\n\nL'écriture a déjà été validée ; elle ne sera pas répétée.",
            )
            self._refresh()
            self.status_message.emit(
                "Présence enregistrée · confirmation de relecture impossible."
            )
            return

        QMessageBox.warning(
            self._page,
            "Présences",
            message,
        )

    def _refresh(self) -> None:
        if callable(self._refresh_callback) and self._person_id is not None:
            self._refresh_callback(self._person_id)
