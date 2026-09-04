from infrastructure.persistence.questionnaire_reader import QuestionnaireReader


class QuestionnaireDB:
    def __init__(self):
        self.requests = []
        self.current = ""
        self.closed = False

    def ExecuterReq(self, req):
        self.current = req
        self.requests.append(req)

    def ResultatReq(self):
        if "FROM questionnaire_categories" in self.current:
            return [
                (1, 0, 1, "(240,240,240)", "Administratif", 10, 0, 1, "Permis", "case_coche", "0", "", 100, "1"),
                (1, 0, 1, "(240,240,240)", "Administratif", 11, 1, 1, "Taille", "liste_deroulante", None, "", None, None),
            ]
        if "FROM questionnaire_choix" in self.current:
            return [
                (501, 11, 0, 1, "S"),
                (502, 11, 1, 1, "M"),
            ]
        return []

    def Close(self):
        self.closed = True


def test_questionnaire_reader_reprend_structure_historique_et_reponse_individu():
    db = QuestionnaireDB()
    reader = QuestionnaireReader(db_factory=lambda: db)

    questions = reader.lire_questionnaire_individu(12)

    assert [item.IDquestion for item in questions] == [10, 11]
    assert questions[0].categorie_label == "Administratif"
    assert questions[0].question_label == "Permis"
    assert questions[0].controle == "case_coche"
    assert questions[0].IDreponse == 100
    assert questions[0].reponse == "1"
    assert [choice.IDchoix for choice in questions[1].choix] == [501, 502]
    assert [choice.label for choice in questions[1].choix] == ["S", "M"]

    questionnaire_sql = db.requests[0]
    assert "questionnaire_categories.type='individu'" in questionnaire_sql
    assert "questionnaire_reponses.IDindividu=12" in questionnaire_sql
    assert "SELECT *" not in questionnaire_sql.upper()
    assert "ORDER BY questionnaire_categories.ordre, questionnaire_questions.ordre" in questionnaire_sql


def test_questionnaire_reader_ne_charge_pas_les_choix_si_aucune_question():
    class EmptyDB(QuestionnaireDB):
        def ResultatReq(self):
            return []

    db = EmptyDB()
    reader = QuestionnaireReader(db_factory=lambda: db)

    assert reader.lire_questionnaire_individu(12) == []
    assert len(db.requests) == 1


def test_questionnaire_reader_refuse_un_identifiant_invalide():
    reader = QuestionnaireReader(db_factory=lambda: QuestionnaireDB())

    for value in (None, True, 0, -1, "abc"):
        try:
            reader.lire_questionnaire_individu(value)
        except ValueError:
            pass
        else:
            raise AssertionError(f"{value!r} aurait dû être refusé")


def test_questionnaire_reader_ferme_sa_connexion():
    db = QuestionnaireDB()
    reader = QuestionnaireReader(db_factory=lambda: db)

    reader.lire_questionnaire_individu(12)
    reader.close()

    assert db.closed is True
