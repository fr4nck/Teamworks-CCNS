from __future__ import annotations

from PySide6.QtWidgets import QLabel, QLineEdit, QWidget

from ui.common import ChoiceSpec, TwChoiceStrip, TwDialogShell, TwFieldRow, TwFormSection


class CoordinatesPreviewDialog(TwDialogShell):
    """Transposition de DLG_Saisie_coords, interactive mais sans persistance."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            "Coordonnées",
            parent,
            profile="compact",
            primary_label="Valider",
            cancel_label="Fermer",
        )

        host = QWidget()
        from PySide6.QtWidgets import QVBoxLayout

        root = QVBoxLayout(host)
        root.setContentsMargins(0, 0, 0, 0)

        note = QLabel("Aperçu Qt de la fiche historique · aucune écriture en base")
        note.setProperty("muted", True)
        root.addWidget(note)

        category_section = TwFormSection("1. Sélectionnez une catégorie")
        self.category = TwChoiceStrip(
            [
                ChoiceSpec("Fixe", "Fixe"),
                ChoiceSpec("Mobile", "Mobile"),
                ChoiceSpec("Fax", "Fax"),
                ChoiceSpec("Email", "Email"),
            ]
        )
        self.category.valueChanged.connect(self._on_category_changed)
        category_section.add_widget(self.category)
        root.addWidget(category_section)

        info_section = TwFormSection("2. Saisissez les informations")
        self.phone = QLineEdit()
        self.phone.setPlaceholderText("Numéro de téléphone")
        self.phone_row = TwFieldRow("N° téléphone", self.phone)
        info_section.add_row(self.phone_row)

        self.email = QLineEdit()
        self.email.setPlaceholderText("adresse@exemple.fr")
        self.email_row = TwFieldRow("Email", self.email)
        self.email_row.setVisible(False)
        info_section.add_row(self.email_row)

        self.label = QLineEdit()
        self.label.setPlaceholderText("Ex. Domicile, contact à Rennes…")
        self.label_row = TwFieldRow("Intitulé", self.label)
        info_section.add_row(self.label_row)
        root.addWidget(info_section)
        root.addStretch(1)

        self.set_content(host)
        self._set_fields_enabled(False)
        # Tant que la persistance Qt n'est pas raccordée, aucun bouton ne peut écrire.
        self.set_primary_enabled(False)

    def _set_fields_enabled(self, enabled: bool) -> None:
        self.phone.setEnabled(enabled)
        self.email.setEnabled(enabled)
        self.label.setEnabled(enabled)

    def _on_category_changed(self, category: str) -> None:
        self._set_fields_enabled(True)
        email_mode = category == "Email"
        self.email_row.setVisible(email_mode)
        self.phone_row.setVisible(not email_mode)
        if email_mode:
            self.email.setFocus()
        else:
            self.phone.setPlaceholderText(f"N° {category}")
            self.phone.setFocus()
