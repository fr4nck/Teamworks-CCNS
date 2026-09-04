# CRH-30 — nouvelle démarche depuis le cockpit RH

## Objet

CRH-30 raccorde la frontière de création contrôlée CRH-29 au cockpit wxPython **Démarches RH**. Le lot rend la création utilisable depuis l'interface sans déplacer la logique métier ou transactionnelle dans wxPython.

## Parcours utilisateur

Le cockpit expose un bouton **Nouvelle démarche** indépendant de la sélection courante. Le runtime de création et le dialogue associé ne sont chargés qu'au premier clic.

Le formulaire demande explicitement :

- le sujet : salarié ou structure ;
- le salarié lorsque le sujet est une personne, à partir des identités réellement présentes dans la base Teamworks ;
- l'organisme, limité aux profils déjà configurés dans **Organismes & connexions RH** ;
- le libellé du type de démarche et son code interne ;
- la date d'ouverture ;
- une échéance facultative ;
- les pièces attendues facultatives ;
- un commentaire facultatif.

Les pièces attendues utilisent la syntaxe explicite `code | libellé | obligatoire/facultative`. Aucun caractère obligatoire n'est déduit si l'utilisateur ne l'indique pas.

Après validation du formulaire, une seconde confirmation est exigée. La création ouvre le dossier au statut métier **À faire**, conserve l'état technique **Non applicable**, ajoute l'événement d'audit `CASE_CREATED`, puis recharge le cockpit en sélectionnant le nouveau dossier.

## Sélection des personnes et organismes

`HrCaseCreationRuntime` expose deux projections minimales :

- `HrCaseCreationPersonOption(identifier, label)` ;
- `HrCaseCreationOrganizationOption(code, label)`.

Les personnes sont lues par `PersonReader`, puis le reader est refermé immédiatement. L'interface ne reçoit ni connexion DB, ni objet historique de personne complet.

Les organismes proviennent exclusivement des profils persistés de la structure active. Un organisme absent de la configuration ne peut donc pas être choisi dans le formulaire ; CRH-29 conserve en plus son contrôle côté service.

## Chargement différé

Le cockpit n'importe ni `HrCaseCreationRuntimeFactory`, ni `DLG_Demarches_rh_creation` au chargement normal :

- le runtime est importé dans `_get_creation_runtime()` ;
- le dialogue est importé dans `OnNewCase()` ;
- l'ouverture du cockpit en lecture seule ne déclenche aucune écriture CRH-29 et aucune lecture de la liste des personnes.

## Garde-fous

CRH-30 ne contient aucun catalogue réglementaire et ne présélectionne aucune DPAE, DSN, démarche France Travail ou Net-entreprises. Le lot ne décide pas qu'une pièce est juridiquement obligatoire, ne calcule aucune échéance légale et ne déclenche aucune communication réseau.

Le cockpit ne connaît toujours ni `structure_ref`, ni `GestionDB`, ni les repositories de production. Il appelle uniquement `runtime.create(request)` après confirmation utilisateur.

La création ne modifie jamais le statut technique d'échange et n'annonce aucune transmission externe.

## Tests

- `tests/test_hr_case_creation_runtime_options.py` vérifie la projection des personnes et organismes, la fermeture du `PersonReader` et l'absence de fuite de l'identité de structure ;
- `tests/test_hr_case_creation_wiring_policy.py` verrouille le chargement paresseux, le bouton, la confirmation explicite, les frontières architecturales et l'absence de catalogue réglementaire dans le formulaire ;
- la qualification complète doit continuer à couvrir le socle et les parcours critiques Windows avant de replacer la PR sur sa base empilée.

## Limites assumées

Le formulaire est volontairement déclaratif. Il n'existe pas encore de catalogue de types de démarches, de règles d'échéance ou de pièces réglementaires maintenues par version. Ces éléments ne devront être ajoutés qu'avec une source, une date d'effet et une validation métier/juridique explicites.

Aucune fusion automatique n'est autorisée.
