#!/usr/bin/env bash
set -Eeuo pipefail

# Construction hors production depuis les fichiers suivis par Git.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
: "${OUT_DIR:=$ROOT/dist}"
mkdir -p "$OUT_DIR"
OUT_DIR="$(cd "$OUT_DIR" && pwd)"

for cmd in git dpkg-deb python3; do
    command -v "$cmd" >/dev/null || { echo "Commande absente : $cmd" >&2; exit 1; }
done
test -f VERSION && test -f teamworks/Teamworks.py && test -f teamworks/Ctrl/CTRL_Liste_fichiers.py
python3 - <<'PY'
from pathlib import Path
s=Path('teamworks/Ctrl/CTRL_Liste_fichiers.py').read_text()
assert 'self.InsertStringItem(self.GetItemCount(), "")' in s
assert 'self.SetStringItem(index, 1, "")' in s
PY

version="$(head -n1 VERSION | tr -d '\r\n')"
case "$version" in
    *-rc*) debversion="${version/-rc/~rc}" ;;
    *) debversion="$version" ;;
esac
case "$debversion" in
    *[!a-zA-Z0-9.+:~\-]*) echo 'VERSION invalide' >&2; exit 1 ;;
esac
arch="$(dpkg --print-architecture)"
if [[ "$arch" != amd64 ]]; then echo "Architecture non qualifiee : $arch" >&2; exit 1; fi
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
pkg="$work/pkg"
app="$pkg/opt/teamworks-ccns/app"
vendor="$pkg/opt/teamworks-ccns/vendor"
mkdir -p "$app" "$vendor" "$pkg/DEBIAN" "$pkg/usr/bin" "$pkg/usr/share/applications" "$pkg/usr/share/pixmaps"

# Pas de secrets, bases locales, caches ni environnements non suivis.
# Distribution limitée au code et aux ressources nécessaires à l'application.
# N'embarque jamais .github/, docs/, tests/, scripts/, notes ou rapports.
git archive --format=tar HEAD -- VERSION teamworks application domain infrastructure | tar -x -C "$app"

# Bibliotheques supplementaires incorporees a la construction.
# L'installation du paquet lui-meme ne telecharge rien.
if [[ "${TEAMWORKS_DEB_VENDOR:-1}" == 1 ]]; then
    python3 -m venv "$work/build-venv"
    "$work/build-venv/bin/pip" install --disable-pip-version-check --no-cache-dir \
        --target "$vendor" --no-deps \
        'appdirs==1.4.4' 'icalendar==6.3.1' 'mailjet-rest==1.5.1' \
        'mysql-connector-python==9.5.0' 'pycryptodome==3.23.0' \
        'XlsxWriter==3.2.9' 'tzdata==2025.2'
fi

icon=''
for candidate in \
    "$app/teamworks/Static/Images/Branding/Teamworks-CCNS.png" \
    "$app/teamworks/Static/Images/80x80/Logo_tw.png" \
    "$app/teamworks/Static/Images/32x32/Logo.png"; do
    if [[ -f "$candidate" ]]; then icon="$candidate"; break; fi
done
if [[ -z "$icon" ]]; then
    echo 'Logo officiel PNG introuvable, construction refusee' >&2
    exit 1
fi
install -m 644 "$icon" "$pkg/usr/share/pixmaps/teamworks-ccns.png"
cat > "$pkg/usr/bin/teamworks-ccns" <<'LAUNCHER'
#!/bin/sh
APP=/opt/teamworks-ccns/app
cd "$APP/teamworks" || exit 1
export PYTHONPATH="/opt/teamworks-ccns/vendor:$APP${PYTHONPATH:+:$PYTHONPATH}"
export TEAMWORKS_APPEARANCE="${TEAMWORKS_APPEARANCE:-light}"
exec /usr/bin/python3 Teamworks.py "$@"
LAUNCHER
chmod 755 "$pkg/usr/bin/teamworks-ccns"
cat > "$pkg/usr/share/applications/teamworks-ccns.desktop" <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=Teamworks-CCNS
Comment=Gestion des equipes et conventions collectives sport
Exec=/usr/bin/teamworks-ccns
Icon=teamworks-ccns
Terminal=false
Categories=Office;
StartupNotify=true
DESKTOP
cat > "$pkg/DEBIAN/control" <<CONTROL
Package: teamworks-ccns
Version: ${debversion}-1+deb13
Section: office
Priority: optional
Architecture: ${arch}
Maintainer: PMSL <sportsetloisirs@pmsl35.fr>
Depends: python3 (>= 3.13), python3-wxgtk4.0, python3-mysqldb, python3-numpy, python3-pil, python3-reportlab, python3-matplotlib, python3-opencv, python3-dateutil, python3-six, python3-requests
Description: Teamworks-CCNS, gestion associative et CCNS
 Application wxPython pour les equipes et les donnees associatives.
 Donnees MariaDB et configurations personnelles non incluses.
CONTROL
find "$app" -type d -name __pycache__ -prune -exec rm -rf {} +
find "$app" -type f -name '*.pyc' -delete
find "$pkg" -type d -exec chmod 755 {} +
find "$pkg" -type f -exec chmod 644 {} +
chmod 755 "$pkg/usr/bin/teamworks-ccns"
python3 -m compileall -q "$app/teamworks/Ctrl/CTRL_Liste_fichiers.py"
find "$app" -type d -name __pycache__ -prune -exec rm -rf {} +
find "$app" -type f -name '*.pyc' -delete
# Audit bloquant AVANT la création de l'artefact.
python3 packaging/debian/check_privacy.py --stage "$pkg"
output="$OUT_DIR/teamworks-ccns_${debversion}-1+deb13_${arch}.deb"
dpkg-deb --root-owner-group --build "$pkg" "$output"
# Contrôle des octets réellement présents dans le .deb, métadonnées comprises.
python3 packaging/debian/check_privacy.py --deb "$output"
dpkg-deb --info "$output"
sha256sum "$output" > "$output.sha256"
echo "ARTIFACT=$output"
