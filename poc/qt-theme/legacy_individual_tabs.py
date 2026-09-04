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
    Les lectures métier restent à raccorder progressivement ; les écritures restent
    désactivées pendant le POC.
    """

    def __init__(self, icon_loader):
        self.icon_loader = icon_loader

    def questionnaire(self):
        return QuestionnairePage()

    def qualifications(self):
        return QualificationsPage(self.icon_loader)

    def presences(self):
        return PresencesPage(self.icon_loader)

    def scenarios(self):
        return ScenariosPage(self.icon_loader)

    def expenses(self):
        return ExpensesPage(self.icon_loader)

    def recruitment(self):
        return RecruitmentPage(self.icon_loader)
