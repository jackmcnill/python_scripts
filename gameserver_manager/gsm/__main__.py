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
    sub.add_parser("passwd", help="Passwort der Weboberfläche ändern")
    args = parser.parse_args()

    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    if args.command == "passwd":
        password = getpass.getpass("Neues Passwort: ")
        if len(password) < 8 or password != getpass.getpass("Wiederholen: "):
            sys.exit("Passwörter stimmen nicht überein oder sind kürzer als 8 Zeichen.")
        config.ensure_auth()
        config.set_password(password)
        print("Passwort geändert.")
        return

    import uvicorn
    from .web import Context, create_app

    new_password = config.ensure_auth()
    if new_password:
        print(f"\nErster Start. Passwort für die Weboberfläche: {new_password}\n"
              "(ändern mit: python -m gsm passwd)\n")
    if args.host not in ("127.0.0.1", "localhost", "::1"):
        print("WARNUNG: Die Oberfläche ist über das Netzwerk erreichbar, aber unverschlüsselt (HTTP).\n"
              "Setze einen Reverse-Proxy mit HTTPS davor oder nutze einen VPN/SSH-Tunnel.\n")
    ctx = Context()
    print(f"Runtime: {ctx.runtime.name} | Daten: {config.DATA_DIR}")
    ctx.start_background()
    uvicorn.run(create_app(ctx), host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
