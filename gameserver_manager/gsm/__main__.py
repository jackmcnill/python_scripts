"""Startpunkt: python -m gsm serve | passwd"""
import argparse
import getpass
import sys

from . import config


def main():
    parser = argparse.ArgumentParser(prog="gsm", description="Game Server Manager")
    sub = parser.add_subparsers(dest="command", required=True)
    serve = sub.add_parser("serve", help="Weboberfläche starten")
    serve.add_argument("--host", default="127.0.0.1", help="Standard: nur lokal (127.0.0.1)")
    serve.add_argument("--port", type=int, default=8080)
    serve.add_argument("--trusted-proxies", default="127.0.0.1",
                       help="Adressen von Reverse-Proxys, deren X-Forwarded-*-Header vertraut wird (Standard: 127.0.0.1)")
    passwd = sub.add_parser("passwd", help="Passwort eines Benutzers setzen (z.B. wenn das Admin-Passwort verloren ging)")
    passwd.add_argument("username", nargs="?", default="admin")
    adduser = sub.add_parser("adduser", help="Benutzer anlegen")
    adduser.add_argument("username")
    adduser.add_argument("--admin", action="store_true", help="als Administrator")
    args = parser.parse_args()

    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    from .users import UserError, UserStore

    store = UserStore()
    if args.command in ("passwd", "adduser"):
        password = getpass.getpass("Passwort: ")
        if password != getpass.getpass("Wiederholen: "):
            sys.exit("Passwörter stimmen nicht überein.")
        try:
            if args.command == "passwd":
                store.update(args.username, password=password)
                print(f"Passwort für '{args.username}' geändert.")
            else:
                store.create(args.username, password, "admin" if args.admin else "user")
                print(f"Benutzer '{args.username}' angelegt.")
        except (UserError, KeyError) as exc:
            sys.exit(f"Fehler: {exc.args[0]}")
        return

    import uvicorn
    from .web import Context, create_app

    created = store.ensure_admin()
    if created and created[1]:
        print(f"\nErster Start. Anmeldung mit Benutzer '{created[0]}' und Passwort: {created[1]}\n"
              "Weitere Benutzer legst du in der Weboberfläche unter 'Benutzer' an.\n")
    if args.host not in ("127.0.0.1", "localhost", "::1"):
        print("WARNUNG: Die Oberfläche ist über das Netzwerk erreichbar, aber unverschlüsselt (HTTP).\n"
              "Setze einen Reverse-Proxy mit HTTPS davor oder nutze einen VPN/SSH-Tunnel.\n")
    ctx = Context()
    print(f"Runtime: {ctx.runtime.name} | Daten: {config.DATA_DIR}")
    ctx.start_background()
    uvicorn.run(create_app(ctx), host=args.host, port=args.port, log_level="warning",
                proxy_headers=True, forwarded_allow_ips=args.trusted_proxies)


if __name__ == "__main__":
    main()
