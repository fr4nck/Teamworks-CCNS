from __future__ import annotations

from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import QLabel, QLineEdit, QVBoxLayout, QWidget

from ui.common import (
    ChoiceSpec,
    SearchModeSpec,
    TwChoiceStrip,
    TwCrudPanel,
    TwDialogShell,
    TwFieldRow,
    TwFormSection,
    TwSearchPicker,
)


_READONLY_NOTE = "Aperçu Qt de la fiche historique · aucune écriture en base"


def _readonly_note() -> QLabel:
    note = QLabel(_READONLY_NOTE)
    note.setProperty("muted", True)
    note.setWordWrap(True)
    return note


def _empty_model(headers: list[str]) -> QStandardItemModel:
    model = QStandardItemModel(0, len(headers))
    model.setHorizontalHeaderLabels(headers)
    return model


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
        root = QVBoxLayout(host)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(_readonly_note())

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


class CitiesPreviewDialog(TwDialogShell):
    """Transposition de DLG_Gestion_villes : rechercher, choisir ou saisir manuellement."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            "Gestion des villes",
            parent,
            profile="wide",
            primary_label="Valider",
            cancel_label="Fermer",
        )
        host = QWidget()
        root = QVBoxLayout(host)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(_readonly_note())

        search_section = TwFormSection(
            "Recherche",
            description="Recherchez une ville ou un code postal dans la base française, puis sélectionnez le résultat.",
        )
        self.search_picker = TwSearchPicker(
            model=_empty_model(["Code postal", "Nom de la ville"]),
            modes=[
                SearchModeSpec("contains", "Une partie du nom"),
                SearchModeSpec("phonetic", "Recherche phonétique"),
            ],
            placeholder="Ville ou code postal",
        )
        search_section.add_widget(self.search_picker, 1)
        root.addWidget(search_section, 1)

        manual = TwFormSection(
            "Saisie manuelle",
            description="À utiliser uniquement si la ville n'est pas présente dans la base.",
        )
        self.manual_postcode = QLineEdit()
        self.manual_city = QLineEdit()
        manual.add_row(TwFieldRow("Code postal", self.manual_postcode))
        manual.add_row(TwFieldRow("Nom de la ville", self.manual_city))
        root.addWidget(manual)

        self.set_content(host)
        self.set_primary_enabled(False)


class CountryEditPreviewDialog(TwDialogShell):
    """Transposition de DLG_Saisie_pays."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            "Pays et nationalité",
            parent,
            profile="compact",
            primary_label="Valider",
            cancel_label="Fermer",
        )
        host = QWidget()
        root = QVBoxLayout(host)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(_readonly_note())

        form = TwFormSection("Pays et nationalité")
        self.country = QLineEdit()
        self.nationality = QLineEdit()
        form.add_row(TwFieldRow("Nom du pays", self.country))
        form.add_row(TwFieldRow("Nationalité", self.nationality))
        root.addWidget(form)
        root.addStretch(1)

        self.set_content(host)
        self.set_primary_enabled(False)


class CountriesPreviewDialog(TwDialogShell):
    """Transposition de DLG_Config_pays avec le patron CRUD commun."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            "Pays et nationalités",
            parent,
            profile="wide",
            primary_label="Fermer",
            cancel_label="Fermer",
        )
        self.primary_button.setVisible(False)
        host = QWidget()
        root = QVBoxLayout(host)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(_readonly_note())

        model = _empty_model(["Nom", "Nationalité", "Nb titulaires"])
        self.crud = TwCrudPanel(
            "Pays et nationalités",
            model=model,
            description="Ajoutez, modifiez ou supprimez les pays et les nationalités correspondantes.",
        )
        self.crud.addRequested.connect(self._open_editor)
        root.addWidget(self.crud, 1)
        self.set_content(host)

    def _open_editor(self) -> None:
        CountryEditPreviewDialog(self).exec()


class SocialSituationsPreviewDialog(TwDialogShell):
    """Transposition de DLG_Config_situations avec le même patron CRUD."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            "Situations sociales",
            parent,
            profile="wide",
            primary_label="Fermer",
            cancel_label="Fermer",
        )
        self.primary_button.setVisible(False)
        host = QWidget()
        root = QVBoxLayout(host)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(_readonly_note())

        model = _empty_model(["Nom de la situation sociale", "Nb titulaires"])
        self.crud = TwCrudPanel(
            "Situations sociales",
            model=model,
            description="Types de situations utilisés dans les fiches personnes : étudiant, retraité, employé…",
        )
        root.addWidget(self.crud, 1)
        self.set_content(host)
