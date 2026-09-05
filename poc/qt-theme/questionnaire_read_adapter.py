from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from infrastructure.persistence.questionnaire_reader import QuestionnaireReader


EMPTY = "—"
DOCUMENT_SENTINEL = "##DOCUMENTS##"


@dataclass(frozen=True)
class QuestionnaireView:
    question: str
    answer: str


class QuestionnaireProductionReadAdapter:
    """Projection lecture seule du questionnaire historique vers l'UI Qt."""

    def __init__(self, reader=None):
        self._reader = reader or QuestionnaireReader()
        self._closed = False

    def list_questionnaire(self, person_id: int) -> Sequence[QuestionnaireView]:
        if self._closed:
            raise RuntimeError("Adaptateur questionnaire déjà fermé")
        records = self._reader.lire_questionnaire_individu(person_id)
        views = []
        for record in records:
            if not _is_visible(record.categorie_visible) or not _is_visible(record.question_visible):
                continue
            # Le wx historique utilise la présence de la ligne de réponse, pas la
            # vérité de son contenu : une réponse enregistrée vide doit donc
            # écraser le défaut au lieu de le ressusciter.
            answer = record.reponse if record.IDreponse is not None else record.defaut
            views.append(
                QuestionnaireView(
                    question=_text(record.question_label),
                    answer=_format_answer(record, answer),
                )
            )
        return tuple(views)

    def close(self) -> None:
        if self._closed:
            return
        self._reader.close()
        self._closed = True


def _is_visible(value) -> bool:
    return value not in (0, False, "0", "False", "false")


def _text(value) -> str:
    if value is None:
        return EMPTY
    text = str(value).strip()
    return text or EMPTY


def _format_answer(record, value) -> str:
    # Le contrôle historique Documents stocke cette sentinelle uniquement pour
    # déclencher la sauvegarde de ses vignettes. Elle n'est jamais une réponse
    # métier et ne doit pas fuiter dans la consultation Qt.
    if record.controle == "documents" or value == DOCUMENT_SENTINEL:
        return "Document(s) associé(s)" if record.IDreponse is not None else EMPTY

    if value in (None, ""):
        return EMPTY
    text = str(value).strip()
    if not text:
        return EMPTY

    choices = {
        str(choice.IDchoix): _text(choice.label)
        for choice in record.choix
        if _is_visible(choice.visible)
    }
    if not choices:
        return text

    ids = [part.strip() for part in text.split(";") if part.strip()]
    labels = [choices[item] for item in ids if item in choices]
    if labels and len(labels) == len(ids):
        return ", ".join(labels)
    return text
