#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from collections import defaultdict
from typing import Callable, Optional

from domain.repositories.questionnaire_data import (
    QuestionnaireChoiceRecord,
    QuestionnaireQuestionRecord,
)
from teamworks.Utils import UTILS_Diagnostic_performance as DiagnosticPerformance


class QuestionnaireReader:
    """Lecteur SQL du questionnaire individuel historique, sans dépendance wxPython."""

    def __init__(self, db_factory: Optional[Callable[[], object]] = None):
        self._db_factory = db_factory or self._default_db_factory
        self._db = None

    @staticmethod
    def _default_db_factory():
        import GestionDB

        return GestionDB.DB()

    @property
    def db(self):
        if self._db is None:
            self._db = self._db_factory()
        return self._db

    @staticmethod
    def _person_id(value) -> int:
        if value is None or isinstance(value, bool):
            raise ValueError("IDpersonne historique obligatoire")
        try:
            result = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("IDpersonne historique invalide") from exc
        if result <= 0:
            raise ValueError("IDpersonne historique invalide")
        return result

    def _fetch(self, req: str, nom_mesure: str):
        with DiagnosticPerformance.mesurer("sql", nom_mesure, {"reader": "QuestionnaireReader"}):
            self.db.ExecuterReq(req)
            return self.db.ResultatReq()

    def lire_questionnaire_individu(self, IDpersonne) -> list[QuestionnaireQuestionRecord]:
        """Lit catégories, questions, choix et réponses du questionnaire de la personne."""
        person_id = self._person_id(IDpersonne)
        req = (
            "SELECT questionnaire_categories.IDcategorie, questionnaire_categories.ordre, "
            "questionnaire_categories.visible, questionnaire_categories.couleur, "
            "questionnaire_categories.label, questionnaire_questions.IDquestion, "
            "questionnaire_questions.ordre, questionnaire_questions.visible, "
            "questionnaire_questions.label, questionnaire_questions.controle, "
            "questionnaire_questions.defaut, questionnaire_questions.options, "
            "questionnaire_reponses.IDreponse, questionnaire_reponses.reponse "
            "FROM questionnaire_categories "
            "INNER JOIN questionnaire_questions ON "
            "questionnaire_questions.IDcategorie=questionnaire_categories.IDcategorie "
            "LEFT JOIN questionnaire_reponses ON "
            "questionnaire_reponses.IDquestion=questionnaire_questions.IDquestion "
            "AND questionnaire_reponses.IDindividu=%d "
            "WHERE questionnaire_categories.type='individu' "
            "ORDER BY questionnaire_categories.ordre, questionnaire_questions.ordre;" % person_id
        )
        rows = self._fetch(req, "QuestionnaireReader.lire_questionnaire_individu")
        if not rows:
            return []

        choix_req = (
            "SELECT IDchoix, IDquestion, ordre, visible, label FROM questionnaire_choix "
            "ORDER BY IDquestion, ordre;"
        )
        choix_rows = self._fetch(choix_req, "QuestionnaireReader.lire_choix")
        choix_par_question: dict[int, list[QuestionnaireChoiceRecord]] = defaultdict(list)
        for row in choix_rows:
            choix = QuestionnaireChoiceRecord(*row)
            choix_par_question[choix.IDquestion].append(choix)

        records = []
        for row in rows:
            question_id = int(row[5])
            records.append(
                QuestionnaireQuestionRecord(
                    *row,
                    choix=tuple(choix_par_question.get(question_id, ())),
                )
            )
        return records

    def close(self) -> None:
        if self._db is not None:
            self._db.Close()
            self._db = None
