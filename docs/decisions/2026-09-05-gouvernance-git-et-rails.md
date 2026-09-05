# Gouvernance Git et rails Teamworks

Date de référence : 2026-09-05

Ce document sauvegarde les règles de travail validées avant nettoyage des conversations. Lorsqu'une information d'état GitHub vieillit, l'état réel du dépôt prévaut. Les règles de gouvernance ci-dessous restent la référence tant qu'elles ne sont pas remplacées explicitement dans Git.

## 1. Rails durables

- `wx/master` = rail wxPython de production et de référence historique.
- `qt/master` = rail durable de migration et d'évolution Qt.
- `master` reste temporairement conservé pour compatibilité avec les workflows, scripts et habitudes historiques, jusqu'à décision explicite de retrait.

## 2. Sens de propagation

- Les corrections métier communes, conformité CCNS, sécurité, compatibilité production et corrections wx nécessaires sont d'abord intégrées côté `wx/master` lorsque leur origine est la production wx.
- Les éléments métier réutilisables sont ensuite propagés de façon contrôlée de `wx/master` vers `qt/master`.
- Les travaux purement UI/runtime Qt ciblent `qt/master`.
- Il n'existe pas de propagation automatique Qt → wx.

## 3. Politique UI

- wxPython reste la référence de production tant que la migration n'est pas achevée.
- On corrige les défauts wx nécessaires ; on évite les grandes refontes UI wx devenues sans intérêt stratégique.
- Les nouveaux développements UI structurants ont vocation à être réalisés en Qt.
- La migration Qt est progressive : écran par écran et domaine par domaine.

## 4. Métier et persistance

- Le rail Qt ne doit pas dupliquer arbitrairement SQL, règles métier ou conventions historiques déjà isolables dans une frontière commune.
- Une règle historique wx n'est pas automatiquement normative : un comportement peut être un bug et doit alors être corrigé ou arbitré avant reproduction.
- Les frontières métier/persistance doivent être pensées pour rester réutilisables par les deux rails lorsque cela est raisonnable.

## 5. Pull requests et intégration

- Aucune PR n'est mergée automatiquement parce que la CI est verte.
- Toute fusion doit être explicitement décidée.
- Les anciennes PR peuvent être fermées sans merge lorsque leur contenu est démontré comme intégré, superseded ou conservé dans une branche de consolidation.
- Les PR de récupération ou de consolidation restent draft tant que leur contenu n'est pas réaligné et requalifié.

## 6. Qualification

Il faut distinguer explicitement :

- CI Linux ;
- CI Windows GitHub ;
- smoke Qt natif qwindows ;
- tests sur base historique versionnée ;
- validation interactive réelle sur poste Windows utilisateur.

Un GO technique automatisé ne vaut pas autorisation de merge ni validation utilisateur terrain.

## 7. Release

- Une qualification Qt réussie ne signifie pas automatiquement qu'un installateur ou une RC Qt est prêt.
- Tant que wx reste le rail de production, une RC de production doit normalement partir de `wx/master`, sauf demande explicite de build de test Qt.
- Les workflows historiques pouvant encore dépendre de `master`, leur cible doit être vérifiée avant toute modification du processus de release.

## 8. Documentation et conversations

- GitHub devient la référence durable : code, tests, docs, issues et PR selon la nature de la décision.
- Une conversation ancienne ne doit pas faire foi contre une décision Git plus récente.
- Toute décision durable prise en conversation doit être matérialisée dans Git avant suppression du chat.
- Les archives de conversations doivent distinguer faits techniques, décisions, hypothèses et états temporaires.

## 9. Portée transverse

Les décisions Teamworks propres au code et à la migration résident dans ce dépôt.

Les décisions transverses concernant Portail, Connecthys, hébergement et infrastructure peuvent également relever de `fr4nck/PMSL-Arch`. Lorsqu'un sujet est transverse, éviter de le redéfinir contradictoirement dans plusieurs dépôts.
