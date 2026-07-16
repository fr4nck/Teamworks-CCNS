# Moteur d'autorisation métier

`AuthorizationService` est le point d'entrée unique pour répondre à la question
suivante : un `Account` actif est-il autorisé à exercer une `Responsibility` sur
un `Scope` donné ?

Le service ne dépend d'aucune couche technique. Il vérifie successivement :

1. que le compte est actif ;
2. qu'un rôle direct, ou une délégation active, porte la responsabilité ;
3. que la combinaison des scopes associés au compte couvre entièrement le scope
   demandé.

Les rôles restent indépendants des périmètres : ils décrivent les
responsabilités, tandis que les scopes attachés à l'`Account` en limitent la
portée. Les nouveaux comptes reçoivent par défaut le scope global afin de
préserver le comportement des comptes créés avant l'introduction du moteur ;
les appelants peuvent fournir des scopes ciblés pour limiter l'habilitation.

```python
authorized = AuthorizationService().authorize(
    account,
    Responsibility.MANAGE_ALSH_PLANNING,
    Scope.for_targets(ScopeKind.SITE, ["Bais"]),
)
```

Les interfaces, l'application et les adaptateurs techniques doivent déléguer
cette décision au service plutôt que de comparer des codes de rôle.
