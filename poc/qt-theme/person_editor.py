"""Compact one-page Qt editor for the first writable employee-details slice."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit,
    QMessageBox, QPlainTextEdit, QVBoxLayout,
)

from application.services.person_generalities_write import (
    PersonDetails,
    PersonDetailsSnapshot,
    validate_person_details,
)


class PersonDetailsEditDialog(QDialog):
    """Edit only the six approved fields; sensitive and linked fields stay read-only."""

    def __init__(self, snapshot: PersonDetailsSnapshot | None, parent=None):
        super().__init__(parent)
        self._validated: PersonDetails | None = None
        creating = snapshot is None
        details = snapshot.details if snapshot is not None else PersonDetails(
            last_name="", first_name="", address=None, postcode=None,
            city=None, memo=None,
        )
        self.setWindowTitle("Créer une fiche salarié" if creating else "Modifier la fiche salarié")
        self.setMinimumWidth(470)

        layout = QVBoxLayout(self)
        label = QLabel(
            ("Nouvelle fiche minimale : nom et prénom obligatoires. "
             "Contrat et informations sociales à compléter ensuite."
             if creating else
             "Identité, adresse et mémo uniquement. Les contrats et les "
             "informations sociales sont conservés sans modification.")
        )
        label.setWordWrap(True)
        layout.addWidget(label)
        form = QFormLayout()
        self.last_name = QLineEdit(details.last_name or "")
        self.last_name.setMaxLength(100)
        self.first_name = QLineEdit(details.first_name or "")
        self.first_name.setMaxLength(100)
        self.address = QPlainTextEdit(details.address or "")
        self.address.setMinimumHeight(60)
        postcode = details.postcode
        if isinstance(postcode, int):
            postcode = str(postcode).zfill(5)
        self.postcode = QLineEdit(str(postcode or ""))
        self.postcode.setMaxLength(5)
        self.city = QLineEdit(details.city or "")
        self.city.setMaxLength(100)
        self.memo = QPlainTextEdit(details.memo or "")
        self.memo.setMinimumHeight(85)

        for text, widget in (
            ("Nom", self.last_name),
            ("Prénom", self.first_name),
            ("Adresse", self.address),
            ("Code postal", self.postcode),
            ("Ville", self.city),
            ("Mémo", self.memo),
        ):
            form.addRow(text, widget)
        layout.addLayout(form)

        controls = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        controls.accepted.connect(self._validate_and_accept)
        controls.rejected.connect(self.reject)
        layout.addWidget(controls)

    def _validate_and_accept(self) -> None:
        try:
            self._validated = validate_person_details(
                last_name=self.last_name.text(),
                first_name=self.first_name.text(),
                address=self.address.toPlainText(),
                postcode=self.postcode.text(),
                city=self.city.text(),
                memo=self.memo.toPlainText(),
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Fiche incomplète", str(exc))
            return
        self.accept()

    def values(self) -> PersonDetails:
        if self._validated is None:
            raise RuntimeError("Aucune validation de la fiche n'a été effectuée.")
        return self._validated
