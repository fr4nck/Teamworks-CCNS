# Publication et conservation de CRH-22 et CRH-36

Le 12 octobre 2026, la publication des portages locaux et le retrait de leurs deux branches historiques sont autorisés après vérification de conservation distante et des archives.

Le code métier qualifié est conservé sur master au commit `53d324b397d44a6ab0f16335c23bbab84709aedb` et sur wx/master au commit `7abda7db20cc4fbc6aaca44cbe522639133dd904`. Le commit documentaire de publication ajoute cette trace sans modifier le code testé. Qt reste inchangé.

Qualification locale : 319 tests du socle et 410 tests wx réussis sous Windows/Linux, deux tests exclusivement SQL réservés à la suite réseau, 12 tests réels réussis sur chacun des serveurs jetables MySQL 5.5.62 et MariaDB 10.11.14 dans la phase de persistance, ainsi que trois parcours natifs de démarches avec six événements d'audit chacun. Les annulations, états périmés, pièces clôturées et échecs d'affichage après écriture sont qualifiés. Aucune recette utilisateur ou qualification d'exécutable distribué n'est revendiquée.

La publication conserve la contrainte de ne pas lancer de CI lourde : son dernier commit porte `[skip ci]`. Ce marqueur évite les workflows push/pull_request concernés ; les qualifications ci-dessus sont locales, pas un succès de CI distante. Voir la [documentation GitHub](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/skip-workflow-runs).

Les apports utiles CRH-22 et les fonctions existantes CRH-36 sont conservés sous les contrats retenus, documentés dans `docs/CRH_CONSERVATION_CRH22_CRH36.md` : schéma version 2, configuration, protection sociale, cockpit, création, transitions, historique et pièces. La fermeture sûre et les généralités récentes de la fiche wx sont conservées. Le paramétrage graphique des modèles de cycle de vie n'est pas créé : il était déjà futur dans CRH-36 ; son domaine, ses services, son repository et ses factories sont conservés.

Archives distantes vérifiées :

- `archive/2026-10-12/three-rails/crh-22-teamworks-hr-cases-persistence` résout `3f50b83b02ce5b93a3e449f4db6c66aed33ce1b9` ;
- `archive/2026-10-12/three-rails/crh-36-lifecycle-template-management` résout `6a75377b1d799c4a710c1f6ecf268efd6955be43`.

Le bundle intégral historique reste intact : `C:\Users\Ordi\Documents\Teamworks-CCNS-full-history-20261012-113949\teamworks-all-refs.bundle`, SHA256 `B2CB79034C18BF465421D80816C2A22673941D2A16A3BDE46AABA6CB76EFE1E2`.

La PR #357 peut être clôturée sans merge après publication et vérification des sommets distants. Les deux branches CRH peuvent ensuite être retirées avec contrôle de leur ancien SHA ; leurs tags et bundles conservent l'historique. Il s'agit d'une conservation fonctionnelle ciblée, pas d'une absorption par filiation Git des 230 commits.

Le `save_case` générique garde sa limite de sauvegarde sans version optimiste. Une migration réelle exige de fermer les anciens binaires et de sauvegarder la base ; aucun retry automatique sur deadlock n'est ajouté.
