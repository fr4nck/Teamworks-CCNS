from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from data_adapter import PersonView
from generalities_satellites import (
    CitiesPreviewDialog,
    CoordinatesPreviewDialog,
    CountriesPreviewDialog,
    SocialSituationsPreviewDialog,
)
from ui.common import (
    ActionSpec,
    TOKENS,
    TwActionBar,
    TwDataTable,
    TwFieldRow,
    TwFormSection,
    ValidationLevel,
)


EMPTY = "—"


def _read_line(text: str = EMPTY, *, disabled: bool = False) -> QLineEdit:
    editor = QLineEdit(text)
    editor.setReadOnly(True)
    editor.setProperty("twReadOnly", True)
    editor.setClearButtonEnabled(False)
    if disabled:
        editor.setEnabled(False)
    return editor


def _secondary_button(label: str, tooltip: str) -> QPushButton:
    button = QPushButton(label)
    button.setObjectName("twSecondaryButton")
    button.setToolTip(tooltip)
    button.setMinimumHeight(TOKENS.controls.height_standard)
    return button


class GeneralitiesPage(QWidget):
    """Transposition Qt de la page historique ``CTRL_Page_generalites``.

    Le composant reproduit les cinq sections de la page réelle (Identité,
    Situation sociale, Adresse, Coordonnées, Mémo) et réutilise le socle commun
    Qt. Il reste strictement en consultation : les satellites peuvent être
    ouverts pour recette visuelle, mais aucune écriture n'est activée.

    Les informations absentes du contrat de lecture courant restent neutres.
    Le NIR n'est volontairement pas chargé par ce POC.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._field_rows: dict[str, TwFieldRow] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        root.addWidget(scroll, 1)

        content = QWidget()
        grid = QGridLayout(content)
        grid.setContentsMargins(
            TOKENS.spacing.sm,
            TOKENS.spacing.sm,
            TOKENS.spacing.sm,
            TOKENS.spacing.sm,
        )
        grid.setHorizontalSpacing(TOKENS.spacing.lg)
        grid.setVerticalSpacing(TOKENS.spacing.lg)
        grid.setColumnStretch(0, 3)
        grid.setColumnStretch(1, 2)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(TOKENS.spacing.lg)
        left_layout.addWidget(self._build_identity())
        left_layout.addWidget(self._build_address())
        left_layout.addStretch(1)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(TOKENS.spacing.lg)
        right_layout.addWidget(self._build_social())
        right_layout.addWidget(self._build_coordinates())
        right_layout.addWidget(self._build_memo(), 1)

        grid.addWidget(left, 0, 0, Qt.AlignmentFlag.AlignTop)
        grid.addWidget(right, 0, 1)
        scroll.setWidget(content)

    def _register_row(self, key: str, row: TwFieldRow) -> TwFieldRow:
        self._field_rows[key] = row
        return row

    def _build_identity(self) -> TwFormSection:
        section = TwFormSection("Identité")

        self.civility = _read_line()
        section.add_row(self._register_row("civility", TwFieldRow("Civilité", self.civility)))

        self.maiden_name = _read_line()
        section.add_row(self._register_row("maiden_name", TwFieldRow("Nom de jeune fille", self.maiden_name)))

        self.last_name = _read_line()
        section.add_row(self._register_row("last_name", TwFieldRow("Nom", self.last_name)))

        self.first_name = _read_line()
        section.add_row(self._register_row("first_name", TwFieldRow("Prénom", self.first_name)))

        self.birth_date = _read_line()
        section.add_row(self._register_row("birth_date", TwFieldRow("Date de naissance", self.birth_date)))

        self.birth_country = _read_line()
        choose_birth_country = _secondary_button("Choisir", "Sélectionner un autre pays de naissance")
        choose_birth_country.clicked.connect(self._open_countries)
        section.add_row(
            self._register_row(
                "birth_country",
                TwFieldRow("Pays de naissance", self.birth_country, action=choose_birth_country),
            )
        )

        self.birth_postcode = _read_line()
        section.add_row(
            self._register_row(
                "birth_postcode",
                TwFieldRow("Code postal de naissance", self.birth_postcode),
            )
        )

        self.birth_city = _read_line()
        search_birth_city = _secondary_button("Rechercher", "Rechercher ou saisir une ville de naissance")
        search_birth_city.clicked.connect(self._open_cities)
        section.add_row(
            self._register_row(
                "birth_city",
                TwFieldRow("Ville de naissance", self.birth_city, action=search_birth_city),
            )
        )

        # Donnée sensible : la page conserve sa place historique mais le POC ne
        # la lit pas. Le contrôle désactivé matérialise explicitement cet état.
        self.nir = _read_line("Non chargé dans le POC", disabled=True)
        nir_row = TwFieldRow(
            "Numéro de sécurité sociale",
            self.nir,
            help_text="Donnée sensible volontairement non chargée dans la couche Qt de consultation.",
        )
        section.add_row(self._register_row("nir", nir_row))

        self.nationality = _read_line()
        choose_nationality = _secondary_button("Choisir", "Sélectionner une autre nationalité")
        choose_nationality.clicked.connect(self._open_countries)
        section.add_row(
            self._register_row(
                "nationality",
                TwFieldRow("Nationalité", self.nationality, action=choose_nationality),
            )
        )
        return section

    def _build_social(self) -> TwFormSection:
        section = TwFormSection("Situation sociale")
        self.social_situation = _read_line()
        manage = _secondary_button("Gérer", "Gérer les situations sociales")
        manage.clicked.connect(self._open_social_situations)
        section.add_row(
            self._register_row(
                "social_situation",
                TwFieldRow("Situation", self.social_situation, action=manage),
            )
        )
        return section

    def _build_address(self) -> TwFormSection:
        section = TwFormSection("Adresse")
        self.address = QPlainTextEdit()
        self.address.setReadOnly(True)
        self.address.setProperty("twReadOnly", True)
        self.address.setMinimumHeight(72)
        section.add_row(self._register_row("address", TwFieldRow("Adresse", self.address)))

        self.postcode = _read_line()
        section.add_row(self._register_row("postcode", TwFieldRow("Code postal", self.postcode)))

        self.city = _read_line()
        search_city = _secondary_button("Rechercher", "Rechercher ou saisir une ville de résidence")
        search_city.clicked.connect(self._open_cities)
        section.add_row(
            self._register_row("city", TwFieldRow("Ville", self.city, action=search_city))
        )
        return section

    def _build_coordinates(self) -> TwFormSection:
        section = TwFormSection("Coordonnées")
        self.coords_model = QStandardItemModel(0, 1, self)
        self.coords_model.setHorizontalHeaderLabels(["Coordonnée"])
        self.coords_table = TwDataTable(model=self.coords_model)
        self.coords_table.horizontalHeader().setVisible(False)
        self.coords_table.setMinimumHeight(118)
        self.coords_table.selectionKeyChanged.connect(self._on_coordinate_selection)
        self.coords_table.activatedKey.connect(lambda _key: self._open_coordinates())
        section.add_widget(self.coords_table)

        self.coords_actions = TwActionBar(
            [
                ActionSpec("add", "Ajouter", "Ajouter.png", "Créer une coordonnée", enabled=True),
                ActionSpec("edit", "Modifier", "Modifier.png", "Modifier la coordonnée sélectionnée", enabled=False),
                ActionSpec(
                    "delete",
                    "Supprimer",
                    "Supprimer.png",
                    "Supprimer la coordonnée sélectionnée",
                    role="destructive",
                    enabled=False,
                ),
            ],
        )
        self.coords_actions.triggered.connect(self._on_coordinate_action)
        section.add_widget(self.coords_actions)
        return section

    def _build_memo(self) -> TwFormSection:
        section = TwFormSection("Mémo")
        self.memo = QPlainTextEdit()
        self.memo.setReadOnly(True)
        self.memo.setProperty("twReadOnly", True)
        self.memo.setMinimumHeight(110)
        section.add_widget(self.memo, 1)
        return section

    def set_person(self, person: PersonView) -> None:
        """Injecte uniquement les informations réellement exposées par l'adaptateur."""
        self.last_name.setText(person.last_name or EMPTY)
        self.first_name.setText(person.first_name or EMPTY)
        self.birth_date.setText(person.birth_date or EMPTY)

        # Les autres champs Généralités ne sont pas encore exposés par le
        # reader canonique. Les laisser neutres interdit toute invention UI.
        for editor in (
            self.civility,
            self.maiden_name,
            self.birth_country,
            self.birth_postcode,
            self.birth_city,
            self.nationality,
            self.social_situation,
            self.postcode,
            self.city,
        ):
            editor.setText(EMPTY)
        self.address.setPlainText("")
        self.memo.setPlainText("")
        self.coords_model.removeRows(0, self.coords_model.rowCount())
        self._on_coordinate_selection(None)
        self.clear_validation_states()

    def clear(self) -> None:
        for editor in (
            self.civility,
            self.maiden_name,
            self.last_name,
            self.first_name,
            self.birth_date,
            self.birth_country,
            self.birth_postcode,
            self.birth_city,
            self.nationality,
            self.social_situation,
            self.postcode,
            self.city,
        ):
            editor.setText(EMPTY)
        self.address.clear()
        self.memo.clear()
        self.coords_model.removeRows(0, self.coords_model.rowCount())
        self._on_coordinate_selection(None)
        self.clear_validation_states()

    def set_field_state(
        self,
        field: str,
        state: ValidationLevel | str,
        message: str = "",
    ) -> None:
        """Point d'entrée presenter -> UI pour erreur/avertissement/succès."""
        self._field_rows[field].set_validation(state, message)

    def clear_validation_states(self) -> None:
        for row in self._field_rows.values():
            row.clear_validation()

    def _on_coordinate_selection(self, key) -> None:
        selected = key is not None
        self.coords_actions.set_enabled("edit", selected)
        self.coords_actions.set_enabled("delete", selected)

    def _on_coordinate_action(self, action_id: str) -> None:
        if action_id in {"add", "edit"}:
            self._open_coordinates()
        # Suppression volontairement non raccordée : aucune écriture dans le POC.

    def _open_coordinates(self) -> None:
        CoordinatesPreviewDialog(self).exec()

    def _open_cities(self) -> None:
        CitiesPreviewDialog(self).exec()

    def _open_countries(self) -> None:
        CountriesPreviewDialog(self).exec()

    def _open_social_situations(self) -> None:
        SocialSituationsPreviewDialog(self).exec()
