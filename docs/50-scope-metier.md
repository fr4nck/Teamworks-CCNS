# Scope métier

`Scope` décrit le périmètre métier sur lequel un `Account` peut exercer ses responsabilités. Il ne porte pas les droits eux-mêmes : les responsabilités restent décrites par les rôles, tandis que le scope limite leur portée d'application.

Le modèle est volontairement générique et réutilisable hors client lourd : il ne dépend ni de wxPython, ni d'une base SQLite, ni de SQLAlchemy, ni d'un accès Web.

## Concepts

- `ScopeKind` énumère des natures génériques de périmètre : association entière (`GLOBAL`), données personnelles (`PERSONAL`), service, site, activité et personne.
- `ScopeAtom` représente une brique de périmètre d'une seule nature. Les périmètres ciblés portent des identifiants fonctionnels sous forme de chaînes normalisées.
- `Scope` agrège un ou plusieurs atomes afin de combiner plusieurs périmètres.

## Opérations métier

- `contains(other)` indique si un périmètre couvre entièrement un autre périmètre.
- `intersects(other)` indique si deux périmètres ont au moins une partie commune.
- `merge(other)` fusionne deux périmètres en conservant les natures génériques.
- `is_global()` détecte la présence d'un périmètre association entière.
- `is_personal()` détecte un périmètre limité strictement aux données personnelles.

## Exemples

Un périmètre peut représenter l'association entière complétée par un service et un site, ou combiner un accès personnel avec une activité. Ces combinaisons restent de simples objets domaine ; l'application décidera ensuite comment appliquer ce filtre aux cas d'usage et aux données disponibles.
