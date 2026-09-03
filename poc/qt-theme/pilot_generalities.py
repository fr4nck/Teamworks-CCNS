from __future__ import annotations

from generalities_page import GeneralitiesPage
from pilot_view import PeopleContractsPilot, _contract_count_text, _initials


class PeopleContractsGeneralitiesPilot(PeopleContractsPilot):
    """Pilote Individus/Contrats avec la vraie composition Généralités Qt.

    Cette sous-classe limite le changement au rail Qt : le reste du pilote reste
    intact tandis que l'ancien `_build_general_tab` est remplacé par le composant
    commun source-grounded.
    """

    def _build_general_tab(self):
        self.generalities_page = GeneralitiesPage(self)
        return self.generalities_page

    def _show_empty_detail(self) -> None:
        super()._show_empty_detail()
        page = getattr(self, "generalities_page", None)
        if page is not None:
            page.clear()

    def _show_person_from_proxy_row(self, proxy_row: int) -> None:
        source_index = self.people_proxy.mapToSource(self.people_proxy.index(proxy_row, 0))
        person = self.people_model.person_at(source_index.row())
        if person is None:
            self._show_empty_detail()
            return

        self.generalities_page.set_person(person)

        contract_key = person.id_historique if person.id_historique is not None else person.id
        self.contracts_model.replace(self.adapter.list_contracts(contract_key))
        contract_count = self.contracts_model.rowCount()
        self.contracts_stack.setCurrentIndex(1 if contract_count else 0)

        historical_id = person.id_historique if person.id_historique is not None else person.id
        self.detail_id.setText(f"{person.contract or 'Aucun contrat en cours'} | ID : {historical_id}")
        self.detail_title.setText(person.name or "—")
        context_parts = [value for value in (person.role, person.site) if value and value != "—"]
        self.detail_context.setText(" · ".join(context_parts) if context_parts else "Adresse / situation : —")
        self.detail_birth.setText(f"Naissance : {person.birth_date or '—'}")
        self.detail_contracts.setText(_contract_count_text(contract_count))
        self.person_avatar.setText(_initials(person.name))
        self.detail_stack.setCurrentIndex(1)
        self.statusBar().showMessage(f"Lecture seule · {person.name} · {contract_count} contrat(s)")
