from __future__ import annotations

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QFont, QImage, QTextDocument
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from application.services.contract_document_workspace import ContractDocumentWorkspace
from domain.documents import GenerationStatus
from document_preview_adapter import preview_twd_template


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

            self.preview_button = QPushButton(
                "Aper\u00e7u du mod\u00e8le TWD"
            )
            self.preview_button.setObjectName("twdPreviewButton")
            self.preview_button.setEnabled(False)
            self.preview_button.clicked.connect(
                self._preview_selected_twd
            )
            self.templates.currentRowChanged.connect(
                lambda _row: self._update_preview_action()
            )
            self.templates.itemDoubleClicked.connect(
                lambda _item: self._preview_selected_twd()
            )
            root.addWidget(self.preview_button)

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
            self._update_preview_action()
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
        self._update_preview_action()

    def _selected_template(self):
        index = self.document_choice.currentIndex()
        if not 0 <= index < len(self.workspace.choices):
            return None

        templates = self.workspace.choices[index].templates
        row = self.templates.currentRow()

        if not 0 <= row < len(templates):
            return None

        return templates[row]

    def _update_preview_action(self):
        template = self._selected_template()
        enabled = bool(
            self.workspace.merge_context is not None
            and template is not None
            and template.location
            and str(template.location).lower().endswith(".twd")
        )
        self.preview_button.setEnabled(enabled)

    def _preview_selected_twd(self):
        template = self._selected_template()
        context = self.workspace.merge_context

        if template is None or context is None:
            return

        try:
            preview = preview_twd_template(template, context)
        except (OSError, ValueError) as exc:
            QMessageBox.warning(
                self, "Aper\u00e7u TWD impossible", str(exc)
            )
            return

        preview_dialog = QDialog(self)
        preview_dialog.setObjectName("twdPreviewDialog")
        preview_dialog.setWindowTitle(
            f"Aper\u00e7u TWD - {template.name}"
        )
        preview_dialog.resize(900, 700)

        layout = QVBoxLayout(preview_dialog)

        banner = QLabel(
            "MODÈLE HISTORIQUE D'EXEMPLE — NON VALIDÉ POUR SIGNATURE"
            if preview.is_example_template
            else "APERÇU EN LECTURE SEULE — AUCUNE GÉNÉRATION ACTIVE",
            preview_dialog,
        )
        banner.setObjectName("twdPreviewQualificationBanner")
        banner.setTextFormat(Qt.TextFormat.PlainText)
        banner.setWordWrap(True)
        layout.addWidget(banner)

        issues = []
        if preview.is_example_template:
            issues.append(
                "Exemple historique : dates fixes et clauses à vérifier "
                "avant tout usage réel."
            )
        if preview.missing_known_fields:
            issues.append(
                "Données métier manquantes : "
                + ", ".join(preview.missing_known_fields)
            )
        if preview.unknown_legacy_tokens:
            issues.append(
                "Variables historiques sans correspondance : "
                + ", ".join(preview.unknown_legacy_tokens)
            )
        issues.extend(
            warning for warning in preview.warnings
            if not warning.startswith("Variables historiques non mappées")
        )

        if preview.unsupported_features:
            issues.append(
                "Fonctions non prises en charge : "
                + ", ".join(preview.unsupported_features)
            )

        if issues:
            label = QLabel("\n".join(issues), preview_dialog)
            label.setTextFormat(Qt.TextFormat.PlainText)
            label.setWordWrap(True)
            layout.addWidget(label)

        browser = QTextBrowser(preview_dialog)
        browser.document().setDefaultFont(QFont("Segoe UI", 10))
        browser.setObjectName("twdPreviewBrowser")
        browser.setOpenLinks(False)
        browser.setOpenExternalLinks(False)

        document = browser.document()
        for asset in preview.assets:
            if not asset.mime_type.startswith("image/"):
                continue

            image = QImage.fromData(asset.to_bytes())
            if not image.isNull():
                document.addResource(
                    QTextDocument.ResourceType.ImageResource,
                    QUrl(asset.uri),
                    image,
                )

        browser.setHtml(preview.html)
        layout.addWidget(browser, 1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close
        )
        buttons.rejected.connect(preview_dialog.reject)
        layout.addWidget(buttons)

        preview_dialog.exec()
