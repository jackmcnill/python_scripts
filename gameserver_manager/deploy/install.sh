#!/usr/bin/env bash
# Installiert den Game Server Manager als Systemdienst (Debian/Ubuntu), optional mit HTTPS über Caddy.
#
#   sudo ./deploy/install.sh --domain manager.beispiel.de     # von außen per HTTPS erreichbar
#   sudo ./deploy/install.sh                                  # nur Dienst auf Port 8080 (z.B. hinter Tunnel/VPN)
#   sudo ./deploy/install.sh --dry-run ...                    # zeigt nur, was passieren würde
set -euo pipefail

DOMAIN=""; PORT=8080; RUN_USER="${SUDO_USER:-}"; DRY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --domain) DOMAIN="$2"; shift 2 ;;
    --port) PORT="$2"; shift 2 ;;
    --user) RUN_USER="$2"; shift 2 ;;
    --dry-run) DRY=1; shift ;;
    -h|--help) sed -n '2,7p' "$0"; exit 0 ;;
    *) echo "Unbekannte Option: $1" >&2; exit 1 ;;
  esac
done

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[ -n "$RUN_USER" ] && [ "$RUN_USER" != "root" ] || { echo "Bitte mit sudo als normaler Benutzer starten (oder --user NAME angeben). Der Manager soll nicht als root laufen." >&2; exit 1; }
[ "$DRY" = 1 ] || [ "$(id -u)" = 0 ] || { echo "Bitte mit sudo ausführen." >&2; exit 1; }
HOME_DIR="$(getent passwd "$RUN_USER" | cut -d: -f6)"
[ -n "$HOME_DIR" ] || { echo "Benutzer '$RUN_USER' existiert nicht." >&2; exit 1; }

run() { if [ "$DRY" = 1 ]; then echo "[dry-run] $*"; else "$@"; fi; }
write() { # write <datei>  (Inhalt über stdin)
  if [ "$DRY" = 1 ]; then echo "[dry-run] schreibe $1:"; sed 's/^/    /'; else cat > "$1"; fi
}

echo "==> Voraussetzungen"
run apt-get update -qq
run apt-get install -y -qq git python3 python3-venv docker.io
if [ "$DRY" != 1 ]; then
  python3 -c 'import sys; sys.exit(sys.version_info < (3, 12))' || { echo "Python 3.12 oder neuer wird benötigt (gefunden: $(python3 --version)). Nutze z.B. Ubuntu 24.04." >&2; exit 1; }
fi
run usermod -aG docker "$RUN_USER"
run systemctl enable --now docker

echo "==> Python-Umgebung"
run sudo -u "$RUN_USER" python3 -m venv "$APP_DIR/.venv"
run sudo -u "$RUN_USER" "$APP_DIR/.venv/bin/pip" install -q -r "$APP_DIR/requirements.txt"

echo "==> Administrator anlegen (falls noch keiner existiert)"
if [ "$DRY" != 1 ]; then
  sudo -H -u "$RUN_USER" bash -c "cd '$APP_DIR' && .venv/bin/python -c \"
from gsm import config
from gsm.users import UserStore
config.DATA_DIR.mkdir(parents=True, exist_ok=True)
r = UserStore().ensure_admin()
if r and r[1]:
    print('    Benutzer: %s   Passwort: %s   (jetzt notieren!)' % r)
else:
    print('    Es gibt bereits Benutzer, nichts geändert.')
\""
fi

# Mit Domain lauscht der Manager nur lokal, nach außen geht es über den HTTPS-Proxy.
BIND="127.0.0.1"; [ -n "$DOMAIN" ] || BIND="0.0.0.0"

echo "==> Systemdienst"
write /etc/systemd/system/gsm.service <<UNIT
[Unit]
Description=Game Server Manager
After=network-online.target docker.service
Wants=network-online.target
Requires=docker.service

[Service]
User=$RUN_USER
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/.venv/bin/python -m gsm serve --host $BIND --port $PORT
Restart=on-failure
RestartSec=3
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
UNIT
run systemctl daemon-reload
run systemctl enable gsm
run systemctl restart gsm

if [ -n "$DOMAIN" ]; then
  echo "==> HTTPS-Proxy (Caddy) für $DOMAIN"
  run apt-get install -y -qq caddy
  write /etc/caddy/Caddyfile <<CADDY
$DOMAIN {
    encode gzip
    reverse_proxy 127.0.0.1:$PORT
}
CADDY
  run systemctl enable caddy
  run systemctl restart caddy
  if command -v ufw >/dev/null 2>&1 && ufw status | grep -q "Status: active"; then
    run ufw allow 80/tcp
    run ufw allow 443/tcp
  fi
  echo
  echo "Fertig. Aufruf: https://$DOMAIN"
  echo "Voraussetzung: Der DNS-Eintrag von $DOMAIN zeigt auf diesen Server und die Ports 80 und 443 sind erreichbar"
  echo "(Router/Firewall). Das Zertifikat holt Caddy automatisch, das kann beim ersten Aufruf einen Moment dauern."
else
  echo
  echo "Fertig. Der Manager läuft auf Port $PORT (unverschlüsselt!). Für den Zugriff von außen:"
  echo "  - erneut mit --domain DEINE.DOMAIN ausführen (empfohlen), oder"
  echo "  - einen Tunnel/VPN verwenden (Tailscale, WireGuard, Cloudflare Tunnel)."
fi
echo
echo "Hinweis: Die Minecraft-Ports deiner Server (z.B. 25565) müssen separat in Firewall/Router freigegeben werden."
echo "Status: systemctl status gsm      Logs: journalctl -u gsm -f"
