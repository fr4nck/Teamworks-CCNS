from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from data_adapter import ContractView, PersonView


class PeopleTableModel(QAbstractTableModel):
    """Modèle Qt de consultation des personnes normalisées par l'adaptateur.

    La couche Qt ne connaît ni repository, ni SQL, ni objet du domaine. Elle reçoit
    uniquement des PersonView immuables et reste donc remplaçable/testable.
    """

    COLUMNS = (
        ("id", "Matricule"),
        ("name", "Nom"),
        ("role", "Fonction"),
        ("classification", "Classification"),
        ("contract", "Contrat"),
        ("weekly_hours", "Temps"),
        ("status", "Statut"),
        ("site", "Site"),
    )

    def __init__(self, people: Sequence[PersonView] = (), parent=None):
        super().__init__(parent)
        self._people = tuple(people)

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._people)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.COLUMNS)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._people):
            return None
        person = self._people[index.row()]
        field_name = self.COLUMNS[index.column()][0]
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            value = getattr(person, field_name)
            return "—" if value in (None, "") else str(value)
        if role == Qt.ItemDataRole.UserRole:
            return person
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal and 0 <= section < len(self.COLUMNS):
            return self.COLUMNS[section][1]
        return section + 1

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def replace(self, people: Sequence[PersonView]) -> None:
        self.beginResetModel()
        self._people = tuple(people)
        self.endResetModel()

    def person_at(self, row: int) -> PersonView | None:
        if 0 <= row < len(self._people):
            return self._people[row]
        return None


class ContractsTableModel(QAbstractTableModel):
    """Modèle Qt de consultation des contrats d'une personne sélectionnée."""

    COLUMNS = (
        ("kind", "Type"),
        ("start", "Début"),
        ("end", "Fin"),
        ("classification", "Classification"),
        ("duration", "Durée"),
        ("status", "Statut"),
    )

    def __init__(self, contracts: Sequence[ContractView] = (), parent=None):
        super().__init__(parent)
        self._contracts = tuple(contracts)

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._contracts)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.COLUMNS)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._contracts):
            return None
        contract = self._contracts[index.row()]
        field_name = self.COLUMNS[index.column()][0]
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            value = getattr(contract, field_name)
            return "—" if value in (None, "") else str(value)
        if role == Qt.ItemDataRole.UserRole:
            return contract
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal and 0 <= section < len(self.COLUMNS):
            return self.COLUMNS[section][1]
        return section + 1

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def replace(self, contracts: Sequence[ContractView]) -> None:
        self.beginResetModel()
        self._contracts = tuple(contracts)
        self.endResetModel()
