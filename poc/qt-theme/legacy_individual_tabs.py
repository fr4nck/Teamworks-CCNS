from __future__ import annotations

from individual_pages import (
    ExpensesPage,
    PresencesPage,
    QualificationsPage,
    QuestionnairePage,
    RecruitmentPage,
    ScenariosPage,
)


class LegacyIndividualTabs:
    """Fabrique des pages Qt de la fiche individuelle historique Teamworks.

    Chaque page visible délègue désormais à un composant dédié et source-grounded.
    Les écritures restent désactivées pendant le POC.
    """

    def __init__(self, icon_loader):
        self.icon_loader = icon_loader
        self.scenarios_page = None
        self.expenses_page = None

    def questionnaire(self):
        return QuestionnairePage()

    def qualifications(self):
        return QualificationsPage(self.icon_loader)

    def presences(self):
        return PresencesPage(self.icon_loader)

    def scenarios(self):
        self.scenarios_page = ScenariosPage(self.icon_loader)
        return self.scenarios_page

    def expenses(self):
        self.expenses_page = ExpensesPage(self.icon_loader)
        return self.expenses_page

    def recruitment(self):
        return RecruitmentPage(self.icon_loader)
