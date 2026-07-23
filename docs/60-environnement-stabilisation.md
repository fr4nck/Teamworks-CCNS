\# Environnement de développement Teamworks-CCNS



Le projet nécessite Python 3.10 minimum.



Version validée pour TW-060 : Python 3.11.



\## Installation Windows



Installer Python 3.11 avec winget :



winget install Python.Python.3.11



Installer les dépendances de test :



py -3.11 -m pip install -r requirements-dev.txt



\## Validation



Depuis la racine du dépôt, lancer :



py -3.11 -m pytest -q



Puis vérifier les imports publics :



py -3.11 -c "import application.control"

py -3.11 -c "import application.presentation"

py -3.11 -c "import infrastructure.persistence"



Puis vérifier les espaces et fins de lignes :



git diff --check



Résultat validé pendant TW-060 :



1007 passed in 2.35s



\## Note Windows



Sous Windows, le paquet tzdata est requis pour les tests utilisant ZoneInfo("Europe/Paris").

Sans tzdata, les tests de disponibilités hebdomadaires échouent avec ZoneInfoNotFoundError.

