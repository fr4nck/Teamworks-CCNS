#!/bin/bash
# Rejoue l'intégration Qt 0.2 : RC #467 + #486 + #450 + #446 + #472.
# Usage : depuis un clone à jour de fr4nck/Teamworks-CCNS
#   bash replay_qt_integration.sh [branche-cible]   (défaut : qt/integration-0.2-rc1)
# Résultat attendu (arbre) : voir EXPECTED_TREE. Aucun ours/theirs : unions sémantiques vérifiées.
# Qualification locale Linux (compileall, UTF-8, socle, audit runtime, pytest) : 2455 passed, 6 skipped ;
# smoke runtime Qt offscreen OK ; benchmark de frugalité OK.
set -euo pipefail
TARGET=${1:-qt/integration-0.2-rc1}
EXPECTED_TREE=2804c6b272d1427bf89fd0b95fcbe3cbf19abe22
declare -A HEADS=(
  [qt/vanilla-0.1-rc]=caed9650df74609f1b0e920fa4d946aa3456cfd8
  [qt/contracts-amendment-foundation]=81f8036851b9232a547b99ec9b1789f04516c056
  [qt/presence-transactions]=de184614c4185c60b3c5526ca4921aa03c2117db
  [qt/scenario-transactions]=46f2b07aed32edf5b034aeb1af708d20362e4a9b
  [architecture/profils-autorisations]=35702a4a40b23bbb4ec77aa94bc896cdd166487e
)
git fetch origin "${!HEADS[@]}"
for b in "${!HEADS[@]}"; do [ "$(git rev-parse origin/$b)" = "${HEADS[$b]}" ] || { echo "HEAD changé : $b — STOP, réauditer"; exit 1; }; done
git checkout -B "$TARGET" "${HEADS[qt/vanilla-0.1-rc]}"
union() { python3 - "$@" <<'PY'
import re,sys
for p in sys.argv[1:]:
    s=open(p).read()
    def f(m):
        a,b=m.group(1),m.group(2)
        if '    ):\n' in a and '    ):\n' in b:   # signature __init__ commune
            a1,a2=a.split('    ):\n',1); b1,b2=b.split('    ):\n',1)
            return a1+b1+'    ):\n'+a2+b2.replace('        self._activity_loader_class = activity_loader_class\n','')
        return a+b
    s,n=re.subn(r'<<<<<<< [^\n]*\n(.*?)=======\n(.*?)>>>>>>> [^\n]*\n',f,s,flags=re.S)
    open(p,'w').write(s); print(p,n)
PY
}
m() { git merge --no-ff --no-commit "${HEADS[$1]}" || true; }
m qt/contracts-amendment-foundation
union .github/workflows/ci.yml poc/qt-theme/pilot_view.py poc/qt-theme/pilot_generalities.py
git add -A; git commit -q -m "Intégration Qt — Contrats avancés (#486) sur la RC Vanilla 0.1 (#467)"
m qt/presence-transactions
union poc/qt-theme/launcher.py poc/qt-theme/pilot_generalities.py
python3 - <<'PY'
p='tests/test_qt_expense_reimbursement_roundtrip.py'; s=open(p).read()
old="    def list_scenarios(self, person_id):\n        return ()\n"; assert s.count(old)==1
open(p,'w').write(s.replace(old,"    def list_presences(self, person_id):\n        return ()\n\n"+old))
PY
git add -A; git commit -q -m "Intégration Qt — Présences (#450)"
git merge --no-ff -q -m "Intégration Qt — Scénarios (#446)" "${HEADS[qt/scenario-transactions]}"
git merge --no-ff -q -m "Intégration Qt — Profils (#472)" "${HEADS[architecture/profils-autorisations]}"
! git grep -n '^<<<<<<<\|^>>>>>>>' || { echo "marqueurs de conflit restants"; exit 1; }
[ "$(git rev-parse HEAD^{tree})" = "$EXPECTED_TREE" ] && echo "ARBRE CONFORME $EXPECTED_TREE" || { echo "ARBRE DIFFÉRENT"; exit 1; }
