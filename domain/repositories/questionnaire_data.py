#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QuestionnaireChoiceRecord:
    IDchoix: int
    IDquestion: int
    ordre: int | None
    visible: int | None
    label: str | None


@dataclass(frozen=True)
class QuestionnaireQuestionRecord:
    IDcategorie: int
    categorie_ordre: int | None
    categorie_visible: int | None
    categorie_couleur: str | None
    categorie_label: str | None
    IDquestion: int
    question_ordre: int | None
    question_visible: int | None
    question_label: str | None
    controle: str | None
    defaut: str | None
    options: str | None
    IDreponse: int | None
    reponse: str | None
    choix: tuple[QuestionnaireChoiceRecord, ...] = ()
