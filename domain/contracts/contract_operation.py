from enum import Enum


class ContractOperation(str, Enum):
    """Nature métier de l'opération qui produit le contrat/avenant.

    Cette information est distincte du type de contrat lui-même : un CDI peut
    être un nouveau contrat ou la poursuite d'un CDD, et un CDD peut être un
    nouveau contrat ou un renouvellement du CDD précédent.
    """

    NEW = "NEW"
    CDD_RENEWAL = "CDD_RENEWAL"
    CDD_TO_CDI = "CDD_TO_CDI"
