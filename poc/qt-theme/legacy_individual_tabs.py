from __future__ import annotations

from collections.abc import Iterable

from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGroupBox,
    QHBoxLayout,
    QTableWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from individual_pages import PresencesPage, QualificationsPage, QuestionnairePage, RecruitmentPage
from legacy_sheets import (
    ReimbursementPreviewDialog,
    ScenarioPreviewDialog,
    TripPreviewDialog,
)


class LegacyIndividualTabs:
    """Transposition visuelle des pages wx historiques de la fiche individuelle.

    Les pages déjà rapprochées du source courant utilisent désormais les
    composants communs Qt. Les autres restent des aperçus historiques en lecture
    seule jusqu'à leur prochain lot de transposition.
    """

    def __init__(self, icon_loader):
        self.icon_loader = icon_loader

    def _tool_button(self, icon_name: str, tooltip: str, fallback: str, dialog_cls=None) -> QToolButton:
        button = QToolButton()
        button.setObjectName("legacyToolButton")
        button.setIcon(self.icon_loader(icon_name))
        button.setIconSize(QSize(16, 16))
        button.setToolTip(tooltip)
        button.setFixedSize(30, 30)
        if button.icon().isNull():
            button.setText(fallback)
        button.setEnabled(dialog_cls is not None)
        if dialog_cls is not None:
            button.clicked.connect(
                lambda _checked=False, cls=dialog_cls, source=button: cls(source.window()).exec()
            )
        return button

    def _table(self, headers: Iterable[str]) -> QTableWidget:
        headers = list(headers)
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(True)
        return table

    def _tool_column(self, specs: Iterable[tuple], *, spacer_after: set[int] | None = None) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        spacer_after = spacer_after or set()
        for index, spec in enumerate(specs):
            icon_name, tooltip, fallback, *extra = spec
            dialog_cls = extra[0] if extra else None
            layout.addWidget(self._tool_button(icon_name, tooltip, fallback, dialog_cls))
            if index in spacer_after:
                layout.addSpacing(8)
        layout.addStretch(1)
        return layout

    def _group_with_table(
        self,
        title: str,
        headers: Iterable[str],
        tools: Iterable[tuple] = (),
        *,
        spacer_after: set[int] | None = None,
    ) -> QGroupBox:
        group = QGroupBox(title)
        layout = QHBoxLayout(group)
        layout.setContentsMargins(8, 10, 8, 8)
        layout.setSpacing(6)
        layout.addWidget(self._table(headers), 1)
        tools = list(tools)
        if tools:
            layout.addLayout(self._tool_column(tools, spacer_after=spacer_after))
        return group

    def questionnaire(self) -> QWidget:
        return QuestionnairePage()

    def qualifications(self) -> QWidget:
        return QualificationsPage(self.icon_loader)

    def presences(self) -> QWidget:
        return PresencesPage(self.icon_loader)

    def scenarios(self) -> QWidget:
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(5, 5, 5, 5)
        root.addWidget(
            self._group_with_table(
                "Scénarios",
                ["Scénario", "Période", "État"],
                [
                    ("Ajouter.png", "Aperçu de la création d'un scénario", "+", ScenarioPreviewDialog),
                    ("Modifier.png", "Modifier le scénario", "M"),
                    ("Supprimer.png", "Supprimer le scénario", "−"),
                    ("Dupliquer.png", "Dupliquer le scénario", "D"),
                ],
                spacer_after={2},
            ),
            1,
        )
        return page

    def expenses(self) -> QWidget:
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(5, 5, 5, 5)
        root.setSpacing(8)
        root.addWidget(
            self._group_with_table(
                "Déplacements",
                ["N°", "Date", "Objet", "Trajet", "Distance", "Tarif", "Montant", "Rmbst"],
                [
                    ("Ajouter.png", "Aperçu de la saisie d'un déplacement", "+", TripPreviewDialog),
                    ("Modifier.png", "Modifier le déplacement", "M"),
                    ("Supprimer.png", "Supprimer le déplacement", "−"),
                    ("Imprimante.png", "Imprimer les déplacements", "I"),
                ],
                spacer_after={2},
            ),
            1,
        )
        root.addWidget(
            self._group_with_table(
                "Remboursements",
                ["N°", "Date", "Montant", "Déplacements rattachés"],
                [
                    ("Ajouter.png", "Aperçu de la saisie d'un remboursement", "+", ReimbursementPreviewDialog),
                    ("Modifier.png", "Modifier le remboursement", "M"),
                    ("Supprimer.png", "Supprimer le remboursement", "−"),
                ],
            ),
            1,
        )
        return page

    def recruitment(self) -> QWidget:
        return RecruitmentPage(self.icon_loader)
