from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate, QTime
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QTimeEdit,
    QVBoxLayout,
)


class PresenceEditorDialog(QDialog):
    """Saisie Qt minimale d'une présence, sans accès DB ni règle métier."""

    def __init__(
        self,
        categories,
        *,
        person_id: int,
        snapshot=None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(
            "Modifier une présence" if snapshot is not None else "Ajouter une présence"
        )
        self.setModal(True)
        self.resize(460, 280)

        root = QVBoxLayout(self)
        form = QFormLayout()

        person = QLabel("Personne n°%d" % int(person_id))
        form.addRow("Personne", person)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        form.addRow("Date", self.date_edit)

        self.start_edit = QTimeEdit()
        self.start_edit.setDisplayFormat("HH:mm")
        form.addRow("Début", self.start_edit)

        self.end_edit = QTimeEdit()
        self.end_edit.setDisplayFormat("HH:mm")
        form.addRow("Fin", self.end_edit)

        self.category_combo = QComboBox()
        for category in categories:
            self.category_combo.addItem(
                category.name or "Catégorie %d" % category.category_id,
                int(category.category_id),
            )
        form.addRow("Catégorie", self.category_combo)

        self.title_edit = QLineEdit()
        self.title_edit.setMaxLength(200)
        form.addRow("Légende", self.title_edit)

        root.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        if snapshot is None:
            today = QDate.currentDate()
            self.date_edit.setDate(today)
            self.start_edit.setTime(QTime(8, 0))
            self.end_edit.setTime(QTime(9, 0))
        else:
            self.date_edit.setDate(
                QDate(
                    snapshot.presence_date.year,
                    snapshot.presence_date.month,
                    snapshot.presence_date.day,
                )
            )
            self.date_edit.setEnabled(False)
            self.start_edit.setTime(QTime.fromString(snapshot.start_time, "HH:mm"))
            self.end_edit.setTime(QTime.fromString(snapshot.end_time, "HH:mm"))
            index = self.category_combo.findData(int(snapshot.category_id))
            if index < 0:
                self.category_combo.addItem(
                    "Catégorie %d (historique)" % int(snapshot.category_id),
                    int(snapshot.category_id),
                )
                index = self.category_combo.count() - 1
            self.category_combo.setCurrentIndex(index)
            self.title_edit.setText(snapshot.title or "")

    def values(self) -> tuple[date, str, str, int, str]:
        qdate = self.date_edit.date()
        return (
            date(qdate.year(), qdate.month(), qdate.day()),
            self.start_edit.time().toString("HH:mm"),
            self.end_edit.time().toString("HH:mm"),
            int(self.category_combo.currentData() or 0),
            self.title_edit.text(),
        )
