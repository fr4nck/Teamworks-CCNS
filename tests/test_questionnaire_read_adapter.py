from domain.repositories.questionnaire_data import (
    QuestionnaireChoiceRecord,
    QuestionnaireQuestionRecord,
)


class FakeReader:
    def __init__(self, records):
        self.records = records
        self.person_ids = []
        self.closed = False

    def lire_questionnaire_individu(self, person_id):
        self.person_ids.append(person_id)
        return list(self.records)

    def close(self):
        self.closed = True


def _question(**changes):
    values = dict(
        IDcategorie=1,
        categorie_ordre=0,
        categorie_visible=1,
        categorie_couleur=None,
        categorie_label="Administratif",
        IDquestion=10,
        question_ordre=0,
        question_visible=1,
        question_label="Taille",
        controle="liste_deroulante",
        defaut="501",
        options=None,
        IDreponse=None,
        reponse=None,
        choix=(
            QuestionnaireChoiceRecord(501, 10, 0, 1, "S"),
            QuestionnaireChoiceRecord(502, 10, 1, 1, "M"),
        ),
    )
    values.update(changes)
    return QuestionnaireQuestionRecord(**values)


def test_questionnaire_adapter_uses_answer_before_default_and_translates_choices():
    from questionnaire_read_adapter import QuestionnaireProductionReadAdapter

    reader = FakeReader((_question(reponse="502", IDreponse=7),))
    adapter = QuestionnaireProductionReadAdapter(reader=reader)

    views = adapter.list_questionnaire(12)

    assert [(view.question, view.answer) for view in views] == [("Taille", "M")]
    assert reader.person_ids == [12]


def test_questionnaire_adapter_uses_default_when_no_saved_answer():
    from questionnaire_read_adapter import QuestionnaireProductionReadAdapter

    adapter = QuestionnaireProductionReadAdapter(reader=FakeReader((_question(),)))

    assert adapter.list_questionnaire(12)[0].answer == "S"


def test_questionnaire_adapter_filters_hidden_question_or_category():
    from questionnaire_read_adapter import QuestionnaireProductionReadAdapter

    reader = FakeReader((
        _question(IDquestion=10, question_visible=0),
        _question(IDquestion=11, categorie_visible=0),
    ))
    adapter = QuestionnaireProductionReadAdapter(reader=reader)

    assert adapter.list_questionnaire(12) == ()


def test_questionnaire_adapter_closes_reader():
    from questionnaire_read_adapter import QuestionnaireProductionReadAdapter

    reader = FakeReader(())
    adapter = QuestionnaireProductionReadAdapter(reader=reader)
    adapter.close()

    assert reader.closed is True
