\# Scénario d'utilisation du contrôle salarial Teamworks-CCNS



Ce document décrit le scénario de validation du module de contrôle salarial au jalon TW-060.



\## Objectif



Vérifier que le parcours complet est utilisable sur une copie de la base PMSL, sans recalcul inutile et sans rupture entre les écrans.



\## Préparation



Avant tout test réel :



\- travailler sur une copie de la base ;

\- conserver une sauvegarde de la base avant lancement ;

\- vérifier que les dépendances Python sont installées ;

\- lancer la suite de tests automatisés.



Commande de validation technique :



py -3.11 -m pytest -q



Résultat validé pendant TW-060 :



1007 passed.



\## Parcours utilisateur à tester



Le scénario complet est le suivant :



1\. ouvrir Teamworks ;

2\. accéder à l'audit CCNS ;

3\. lancer ou consulter le contrôle salarial ;

4\. vérifier les indicateurs salariaux du tableau de bord ;

5\. ouvrir le détail salarial d'un contrat ;

6\. ouvrir la synthèse salariale d'un salarié ;

7\. consulter l'historique des contrôles salariaux ;

8\. comparer deux snapshots ;

9\. consulter le suivi des anomalies ;

10\. consulter les alertes salariales ;

11\. exporter le rapport consolidé en CSV ;

12\. exporter le rapport consolidé en JSON.



\## Résultat attendu



Le module est considéré testable si :



\- aucun écran ne provoque d'erreur bloquante ;

\- les exports CSV et JSON sont générés ;

\- les montants restent cohérents avec les lignes de contrôle ;

\- les snapshots sont consultables sans recalcul métier ;

\- les comparaisons, anomalies et alertes utilisent les résultats historisés ;

\- les données de production ne sont jamais modifiées directement pendant le test.



\## Limites connues hors périmètre TW-060



TW-060 ne couvre pas :



\- la certification juridique des résultats de paie ;

\- la génération automatique des bulletins ;

\- l'envoi automatique d'alertes par mail ;

\- la synchronisation externe avec Net-Entreprises ;

\- l'intégration directe avec un logiciel de paie ;

\- la correction automatique des contrats incomplets ;

\- l'exploitation sur la base PMSL originale sans sauvegarde préalable.



\## Critère de sortie



Le jalon TW-060 est atteint lorsque :



\- les tests automatisés sont verts ;

\- les imports publics sont vérifiés ;

\- le parcours complet est documenté ;

\- les limites connues sont explicites ;

\- une copie de la base PMSL peut être utilisée pour un test réel.

