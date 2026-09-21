from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QListWidget,
    QVBoxLayout,
    QWidget,
)

from application.services.contract_document_workspace import ContractDocumentWorkspace
from domain.documents import GenerationStatus


_STATUS_LABELS = {
    GenerationStatus.READY: "Prêt",
    GenerationStatus.BLOCKED: "Bloqué",
    GenerationStatus.EXTERNAL_PREPARATION: "Préparation externe",
    None: "Indisponible",
}


class ContractDocumentsDialog(QDialog):
    """Consultation du workflow documentaire ; aucune génération Office ici."""

    def __init__(
        self,
        workspace: ContractDocumentWorkspace,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.workspace = workspace
        self.setWindowTitle(
            f"Documents RH · contrat n°{workspace.contract_id or '—'}"
        )
        self.setMinimumWidth(620)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        intro = QLabel(
            "Préparation des documents RH · consultation uniquement. "
            "La génération Word / LibreOffice n'est pas activée dans ce lot."
        )
        intro.setWordWrap(True)
        intro.setProperty("muted", True)
        root.addWidget(intro)

        if workspace.errors:
            error_label = QLabel(
                "\n".join(
                    f"{error.code.value} · {error.message}"
                    for error in workspace.errors
                )
            )
            error_label.setWordWrap(True)
            root.addWidget(error_label)
        else:
            form = QFormLayout()
            self.document_choice = QComboBox()
            for choice in workspace.choices:
                self.document_choice.addItem(choice.label, choice.code)
            self.status_value = QLabel("—")
            self.status_value.setWordWrap(True)
            form.addRow("Document", self.document_choice)
            form.addRow("État", self.status_value)
            root.addLayout(form)

            root.addWidget(QLabel("Modèles compatibles"))
            self.templates = QListWidget()
            root.addWidget(self.templates, 1)

            root.addWidget(QLabel("Contrôles et informations"))
            self.issues = QListWidget()
            root.addWidget(self.issues, 1)

            self.document_choice.currentIndexChanged.connect(
                self._refresh_current_choice
            )
            self._refresh_current_choice()

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        root.addWidget(buttons)

    def _refresh_current_choice(self, *_args) -> None:
        index = self.document_choice.currentIndex()
        if not 0 <= index < len(self.workspace.choices):
            self.status_value.setText("Indisponible")
            self.templates.clear()
            self.issues.clear()
            return

        choice = self.workspace.choices[index]
        status = _STATUS_LABELS.get(choice.status, str(choice.status or "Indisponible"))
        if choice.generated_by_teamworks:
            status += " · modèle interne"
        else:
            status += " · service externe"
        self.status_value.setText(status)

        self.templates.clear()
        for template in choice.templates:
            suffix = " · historique" if template.legacy else ""
            self.templates.addItem(f"{template.name}{suffix}")
        if not choice.templates:
            self.templates.addItem("Aucun modèle compatible")

        self.issues.clear()
        for issue in choice.issues:
            self.issues.addItem(issue)
        if not choice.issues:
            self.issues.addItem("Aucune anomalie détectée")
