from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QGridLayout,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from data_adapter import PersonGeneralitiesView, PersonView
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
_TWO_COLUMN_MIN_WIDTH = 760


def _read_line(text: str = EMPTY) -> QLineEdit:
    editor = QLineEdit(text)
    editor.setReadOnly(True)
    editor.setProperty("twReadOnly", True)
    editor.setClearButtonEnabled(False)
    return editor


def _secondary_button(label: str, tooltip: str) -> QPushButton:
    button = QPushButton(label)
    button.setObjectName("twSecondaryButton")
    button.setToolTip(tooltip)
    return button


def _empty_layout(layout) -> None:
    while layout.count():
        layout.takeAt(0)


class GeneralitiesPage(QWidget):
    """Transposition Qt de ``CTRL_Page_generalites`` en consultation.

    Les cinq sections historiques sont conservées. Les valeurs proviennent du
    reader dédié ; seules les données effectivement projetées en lecture sont
    représentées dans l'interface.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._field_rows: dict[str, TwFieldRow] = {}
        self._responsive_columns: int | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        root.addWidget(self.scroll, 1)

        content = QWidget()
        self.content_grid = QGridLayout(content)
        self.content_grid.setContentsMargins(
            TOKENS.spacing.xs,
            TOKENS.spacing.xs,
            TOKENS.spacing.xs,
            TOKENS.spacing.xs,
        )
        self.content_grid.setHorizontalSpacing(TOKENS.spacing.md)
        self.content_grid.setVerticalSpacing(TOKENS.spacing.md)

        self.section_identity = self._build_identity()
        self.section_social = self._build_social()
        self.section_address = self._build_address()
        self.section_coordinates = self._build_coordinates()
        self.section_memo = self._build_memo()

        self.left_column = QWidget()
        self.left_layout = QVBoxLayout(self.left_column)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.setSpacing(TOKENS.spacing.md)

        self.right_column = QWidget()
        self.right_layout = QVBoxLayout(self.right_column)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(TOKENS.spacing.md)

        self.scroll.setWidget(content)
        self._apply_responsive_layout(2, force=True)

    def resizeEvent(self, event) -> None:
        columns = 2 if event.size().width() >= _TWO_COLUMN_MIN_WIDTH else 1
        self._apply_responsive_layout(columns)
        super().resizeEvent(event)

    def _apply_responsive_layout(self, columns: int, *, force: bool = False) -> None:
        if not force and columns == self._responsive_columns:
            return

        _empty_layout(self.left_layout)
        _empty_layout(self.right_layout)
        self.content_grid.removeWidget(self.left_column)
        self.content_grid.removeWidget(self.right_column)

        if columns == 1:
            for section in (
                self.section_identity,
                self.section_social,
                self.section_address,
                self.section_coordinates,
                self.section_memo,
            ):
                self.left_layout.addWidget(section)
            self.left_layout.addStretch(1)
            self.right_column.hide()
            self.content_grid.addWidget(self.left_column, 0, 0, 1, 2)
            self.content_grid.setColumnStretch(0, 1)
            self.content_grid.setColumnStretch(1, 0)
        else:
            self.left_layout.addWidget(self.section_identity)
            self.left_layout.addWidget(self.section_address)
            self.left_layout.addStretch(1)

            self.right_layout.addWidget(self.section_social)
            self.right_layout.addWidget(self.section_coordinates)
            self.right_layout.addWidget(self.section_memo, 1)

            self.right_column.show()
            self.content_grid.addWidget(self.left_column, 0, 0, Qt.AlignmentFlag.AlignTop)
            self.content_grid.addWidget(self.right_column, 0, 1)
            self.content_grid.setColumnStretch(0, 3)
            self.content_grid.setColumnStretch(1, 2)

        self._responsive_columns = columns

    def _row(
        self,
        key: str,
        label: str,
        editor: QWidget,
        *,
        action: QWidget | None = None,
        help_text: str | None = None,
    ) -> TwFieldRow:
        row = TwFieldRow(
            label,
            editor,
            action=action,
            help_text=help_text,
            compact=True,
        )
        self._field_rows[key] = row
        return row

    def _build_identity(self) -> TwFormSection:
        section = TwFormSection("Identité", compact=True)
        self.civility = _read_line()
        section.add_row(self._row("civility", "Civilité", self.civility))
        self.maiden_name = _read_line()
        section.add_row(self._row("maiden_name", "Nom de jeune fille", self.maiden_name))
        self.last_name = _read_line()
        section.add_row(self._row("last_name", "Nom", self.last_name))
        self.first_name = _read_line()
        section.add_row(self._row("first_name", "Prénom", self.first_name))
        self.birth_date = _read_line()
        section.add_row(self._row("birth_date", "Date de naissance", self.birth_date))

        self.birth_country = _read_line()
        choose_birth_country = _secondary_button("Choisir", "Sélectionner un autre pays de naissance")
        choose_birth_country.clicked.connect(self._open_countries)
        section.add_row(
            self._row(
                "birth_country",
                "Pays de naissance",
                self.birth_country,
                action=choose_birth_country,
            )
        )

        self.birth_postcode = _read_line()
        section.add_row(self._row("birth_postcode", "Code postal de naissance", self.birth_postcode))

        self.birth_city = _read_line()
        search_birth_city = _secondary_button("Rechercher", "Rechercher ou saisir une ville de naissance")
        search_birth_city.clicked.connect(self._open_cities)
        section.add_row(
            self._row(
                "birth_city",
                "Ville de naissance",
                self.birth_city,
                action=search_birth_city,
            )
        )

        self.nationality = _read_line()
        choose_nationality = _secondary_button("Choisir", "Sélectionner une autre nationalité")
        choose_nationality.clicked.connect(self._open_countries)
        section.add_row(
            self._row(
                "nationality",
                "Nationalité",
                self.nationality,
                action=choose_nationality,
            )
        )
        return section

    def _build_social(self) -> TwFormSection:
        section = TwFormSection("Situation sociale", compact=True)
        self.social_situation = _read_line()
        manage = _secondary_button("Gérer", "Gérer les situations sociales")
        manage.clicked.connect(self._open_social_situations)
        section.add_row(
            self._row(
                "social_situation",
                "Situation",
                self.social_situation,
                action=manage,
            )
        )
        return section

    def _build_address(self) -> TwFormSection:
        section = TwFormSection("Adresse", compact=True)
        self.address = QPlainTextEdit()
        self.address.setReadOnly(True)
        self.address.setProperty("twReadOnly", True)
        self.address.setMinimumHeight(58)
        section.add_row(self._row("address", "Adresse", self.address))

        self.postcode = _read_line()
        section.add_row(self._row("postcode", "Code postal", self.postcode))

        self.city = _read_line()
        search_city = _secondary_button("Rechercher", "Rechercher ou saisir une ville de résidence")
        search_city.clicked.connect(self._open_cities)
        section.add_row(self._row("city", "Ville", self.city, action=search_city))
        return section

    def _build_coordinates(self) -> TwFormSection:
        section = TwFormSection("Coordonnées", compact=True)
        self.coords_model = QStandardItemModel(0, 1, self)
        self.coords_model.setHorizontalHeaderLabels(["Coordonnée"])
        self.coords_table = TwDataTable(model=self.coords_model)
        self.coords_table.horizontalHeader().setVisible(False)
        self.coords_table.setMinimumHeight(96)
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
        section = TwFormSection("Mémo", compact=True)
        self.memo = QPlainTextEdit()
        self.memo.setReadOnly(True)
        self.memo.setProperty("twReadOnly", True)
        self.memo.setMinimumHeight(88)
        section.add_widget(self.memo, 1)
        return section

    def set_person(self, person: PersonView) -> None:
        """Affiche immédiatement l'identité minimale puis attend le détail worker."""
        self.clear()
        self.last_name.setText(person.last_name or EMPTY)
        self.first_name.setText(person.first_name or EMPTY)
        self.birth_date.setText(person.birth_date or EMPTY)

    def set_details(self, details: PersonGeneralitiesView | None) -> None:
        """Injecte les Généralités historiques lues hors du thread UI."""
        if details is None:
            return
        for editor, value in (
            (self.civility, details.civility),
            (self.maiden_name, details.maiden_name),
            (self.last_name, details.last_name),
            (self.first_name, details.first_name),
            (self.birth_date, details.birth_date),
            (self.birth_country, details.birth_country),
            (self.birth_postcode, details.birth_postcode),
            (self.birth_city, details.birth_city),
            (self.nationality, details.nationality),
            (self.social_situation, details.social_situation),
            (self.postcode, details.postcode),
            (self.city, details.city),
        ):
            editor.setText(value or EMPTY)
        self.address.setPlainText(details.address or "")
        self.memo.setPlainText(details.memo or "")

        self.coords_model.removeRows(0, self.coords_model.rowCount())
        for coordinate in details.coordinates:
            item = QStandardItem(coordinate.text or EMPTY)
            item.setData(coordinate.key, Qt.ItemDataRole.UserRole)
            context = " · ".join(
                part for part in (coordinate.category, coordinate.label) if part and part != EMPTY
            )
            if context:
                item.setToolTip(context)
            self.coords_model.appendRow(item)
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

    def _open_coordinates(self) -> None:
        CoordinatesPreviewDialog(self).exec()

    def _open_cities(self) -> None:
        CitiesPreviewDialog(self).exec()

    def _open_countries(self) -> None:
        CountriesPreviewDialog(self).exec()

    def _open_social_situations(self) -> None:
        SocialSituationsPreviewDialog(self).exec()
