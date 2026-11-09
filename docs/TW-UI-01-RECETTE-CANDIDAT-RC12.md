# Teamworks-CCNS — Candidat Windows 0.9.2-rc12 / recette TW-UI-01

**Statut : candidat de recette non publié.**
Le GO reçu autorise la préparation et le contrôle d'un **exécutable isolé**,
pas la publication d'une release ni l'envoi d'un courriel réel.

## 1. Provenance du paquet

- Rail : `wx/master`. Version du code candidat : `0.9.2-rc12`.
- Le workflow existant `.github/workflows/ci.yml` compile le portable via
  le marqueur de commit `[windows]`.
- Le marqueur additionnel `[candidate-only]` inhibe **expressément**
  l'étape « Publier la release GitHub ».
- La construction ne part que si les jobs tests Linux et Windows sont verts.
- L'archive `Teamworks-CCNS-0.9.2-rc12-windows-x64.zip` est remise en
  **artefact du run Actions**, non en release publique.
- Le workflow génère aussi un installeur, mais ce n'est **pas** le support
  à utiliser pour la recette isolée, afin de ne pas écrire dans le profil
  et les chemins d'installation habituels.
- La rétention des artefacts du workflow est actuellement de **3 jours**.
  Un artefact expiré devra être reconstruit ; ne pas substituer un ancien.

## 2. Contrôles avant essai

1. Ouvrir le run GitHub Actions du commit candidat et relever son SHA.
2. Confirmer `SUCCESS` pour les jobs **Tests et règles du socle**,
   **Parcours critiques Windows** et **Paquets Windows portable et installable**.
3. Télécharger l'artefact `Teamworks-CCNS-Windows` dans la section
   « Artifacts » de **ce même run**. Ne pas utiliser une release RC11.
4. Vérifier les SHA-256 de l'archive et de l'installeur contre
   `SHA256SUMS.txt` ; ne pas lancer l'installeur pour cette recette.
5. Décompresser uniquement l'archive portable dans un **nouveau dossier**
   sous `C:\_Atelier_IA\Teamworks-CCNS\Recette-RC12\`.
   Ne rien écrire à la racine de `C:\` ; ne déplacer ni supprimer des
   données ou versions existantes.
6. Vérifier que le `BUILD.txt` du dossier extrait contient le **même SHA**
   que le run GitHub ; vérifier `VERSION` = `0.9.2-rc12`.
7. Employer un **compte utilisateur Windows de test séparé** ou une VM
   et uniquement une base fictive. Le portable peut accéder aux paramètres
   du profil Windows courant : le dossier séparé ne suffit pas à isoler
   les données et les identifiants existants.
8. **Interdire l'accès réseau sortant** pendant la première recette
   graphique, notamment SMTP et Mailjet. N'activer que le serveur de
   messagerie local fictif lorsqu'il est effectivement configuré.
   Ne pas cliquer sur « Envoyer » si le transport fictif n'est pas installé.

## 3. Vérifications pratiques

| Vérification | Attendu |
| --- | --- |
| Démarrage du portable | Fenêtre principale visible, sans crash |
| Fenêtre maximisée | Reste maximisée après ouverture/fermeture du Mailer |
| Fenêtre normale | Pas de maximisation forcée |
| Minimisation volontaire | Possible, puis retour à la fenêtre normale |
| Ouverture et fermeture du Mailer | Aucun dialogue orphelin ni apparition « fantôme » |
| Navigation vers la configuration d'expéditeur | Aucun gel |
| Export Excel vers Mailer | La fenêtre reste rattachée à l'application |
| Tests d'envoi individuel/collectif | **Uniquement** avec le transport fictif |
| Fermeture pendant envoi fictif | Message explicite, aucun envoi doublé |
| Compte-rendu des refus/états incertains | Aucun faux succès ni renvoi automatique |
| Sauvegarde/rapport de crash | Avec dossier et base fictifs seulement |

Pour chaque essai, relever l'état (PASS/FAIL/NON TESTÉ), une capture
anonymisée si utile, le scénario et le SHA de `BUILD.txt`.

## 4. Critères de décision

**GO pour proposer la publication RC12** seulement après :
- construction et démarrage depuis le SHA exact ;
- vérification des parcours critiques dans le véritable portable ;
- contrôle des états Windows (focus, modalité, minimisation) ;
- recette sur base fictive sans résultat métier incorrect ;
- validation explicite de l'utilisateur.

Un test de simulateur SMTP/Mailjet ne prouve pas la livraison finale
d'un courriel. Les tests de véritables serveurs/identifiants sont exclus.

**NO GO publication** si un parcours de mail est encore gelé, si une
fenêtre fantôme est reproduite, si des envois sont dupliqués, si le
paquet n'est pas traçable ou si la recette utilisateur est absente.

## 5. Constat à reporter

SHA du candidat : **à relever dans le run Actions**.

Run Actions : **à relever après déclenchement**.

État de recette utilisateur : **NON TESTÉ** tant qu'aucun essai n'a été
réalisé par l'utilisateur dans son environnement Windows isolé.

Aucun tag, release, envoi réel ou migration SQL autorisé par ce protocole.
