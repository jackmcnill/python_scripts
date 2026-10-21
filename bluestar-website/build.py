#!/usr/bin/env python3
"""Baut die statische BlueStar-Direct-Seite nach dist/ (kein CMS, kein Datenbank-Backend)."""
from pathlib import Path

OUT = Path(__file__).parent / "dist"
YEAR = 2026
NAV = [("index.html", "Home"), ("ueber-uns.html", "Über uns"), ("leistungen.html", "Leistungen"),
       ("emailmarketing.html", "E-Mail-Marketing"), ("kontakt.html", "Kontakt")]

LOGO = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2l2.9 6.6 7.1.7-5.4 4.7 1.6 7L12 17.3 5.8 21l1.6-7L2 9.3l7.1-.7z"/></svg>'

def icon(name):
    paths = {
        "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4"/>',
        "flow": '<path d="M4 6h8v6h8M4 18h8v-6"/>',
        "up": '<path d="M3 17l6-6 4 4 8-8M15 7h6v6"/>',
        "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
        "shield": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/>',
        "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
        "euro": '<path d="M17 6a6 6 0 100 12M4 10h9M4 14h9"/>',
        "chart": '<path d="M4 20V10M10 20V4M16 20v-8M22 20H2"/>',
        "devices": '<rect x="2" y="5" width="14" height="10" rx="1"/><rect x="18" y="8" width="4" height="9" rx="1"/>',
        "inbox": '<path d="M3 13l3-8h12l3 8v6H3zM3 13h5l1 3h6l1-3h5"/>',
        "doc": '<path d="M6 3h9l4 4v14H6zM9 12h7M9 16h7"/>',
        "handshake": '<path d="M2 12l5-5 4 3 4-3 5 5-9 8z"/>',
    }
    return f'<div class="ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{paths[name]}</svg></div>'

def cards(items):
    return '<div class="grid">' + "".join(
        f'<div class="card">{icon(i)}<h3>{t}</h3><p>{p}</p></div>' for i, t, p in items) + "</div>"

def page(fname, title, desc, body, hero=None):
    nav = "".join(f'<li><a href="{h}"{" aria-current=page" if h == fname else ""}>{n}</a></li>' for h, n in NAV)
    return f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} – BlueStar Direct</title><meta name="description" content="{desc}">
<link rel="stylesheet" href="assets/style.css"></head><body>
<a class="skip" href="#main">Zum Inhalt springen</a>
<header class="site"><div class="wrap"><a class="logo" href="index.html">{LOGO}BlueStar Direct</a>
<button class="burger" aria-expanded="false" aria-controls="nav" onclick="var n=document.getElementById('nav');n.classList.toggle('open');this.setAttribute('aria-expanded',n.classList.contains('open'))">Menü</button>
<nav id="nav" aria-label="Hauptmenü"><ul>{nav}</ul></nav></div></header>
<main id="main">{hero or ""}{body}</main>
<footer class="site"><div class="wrap"><div><strong>BlueStar Direct Marketing GmbH</strong><br>Altmarkt 10 B, 01067 Dresden<br>© {YEAR}</div>
<ul><li><a href="datenschutz.html">Datenschutz</a></li><li><a href="impressum.html">Impressum</a></li><li><a href="assets/bluestar_agb_2022_agb_e-mail-kampagnen.pdf">AGB</a></li></ul></div></footer>
</body></html>"""

def phero(h, p):
    return f'<div class="page-hero"><div class="wrap"><h1>{h}</h1><p>{p}</p></div></div>'

CTA = '<section class="alt cta"><div class="wrap"><h2>Lassen Sie uns sprechen</h2><p class="lead" style="margin:auto">Gern erstellen wir Ihnen ein unverbindliches, individuelles Angebot.</p><a class="btn primary" href="kontakt.html">Kontaktieren Sie uns</a></div></section>'

pages = {}

pages["index.html"] = page("index.html", "Home", "E-Mail-Marketing aus Dresden: Zielgruppen erreichen, Leads gewinnen, Umsatz steigern.",
f"""<section><div class="wrap"><h2>Online-Marketing, das ankommt</h2>
{cards([("target","Optimale Zielgruppenansprache","Ihre Botschaft erreicht genau die Menschen, die sich dafür interessieren."),
("flow","Smarte und effiziente Workflows","Schlanke Abläufe von der Planung bis zum Reporting."),
("up","Sales und Leads steigern","Messbare Ergebnisse statt Streuverluste.")])}</div></section>
<section class="alt"><div class="wrap"><h2>Erfolgreiches E-Mail-Marketing mit der BlueStar Direct Marketing GmbH</h2>
<p class="lead">Wir setzen auf Qualität statt auf günstige Anbieter aus dem Ausland mit riesigen, unsauberen Datenbanken.</p>
{cards([("chart","Analysen und Trends","Wir werten Kampagnen aus und leiten daraus Empfehlungen ab."),
("up","Mehr Umsatz","Direkte Ansprache, die Verkäufe auslöst."),
("handshake","Neue Kunden","Erreichen Sie neue Interessenten in Deutschland, Österreich und der Schweiz."),
("mail","Produkte einführen","Neue Produkte gezielt und schnell im Markt platzieren.")])}</div></section>
<section><div class="wrap"><h2>Weshalb Sie sich für BlueStar Direct entscheiden sollten</h2>
{cards([("shield","Rechtssicher","Wir halten die gesetzlichen Vorgaben ein. Sämtliche Empfänger haben ihre Anmeldung per Double-Opt-In bestätigt."),
("target","Hohe Qualität","Ein großer, gepflegter Empfängerpool statt anonymer Massenlisten."),
("handshake","Persönlich","Feste Ansprechpartner und individuelle Lösungen.")])}</div></section>{CTA}""",
hero='<div class="hero"><div class="wrap"><h1>Willkommen bei BlueStar Direct</h1><p>Ihre E-Mail-Marketing-Agentur aus Dresden: persönlich, transparent und erfolgsorientiert.</p><a class="btn" href="kontakt.html">Angebot anfragen</a></div></div>')

pages["ueber-uns.html"] = page("ueber-uns.html", "Über uns", "Die BlueStar Direct Marketing GmbH – E-Mail-Marketing-Agentur in Dresden.",
f"""<section><div class="wrap prose"><h2>Eine Datenbank, viele Möglichkeiten</h2>
<p>Wir verfügen über eine große Datenbank an Interessenten in Deutschland, der Schweiz und Österreich. Empfänger lassen sich nach Kriterien wie Alter, Wohnort und Produktinteressen auswählen.</p>
<h2>Warum E-Mail-Marketing?</h2><ul><li>Funktioniert auf allen Endgeräten</li><li>Erreicht Empfänger direkt</li><li>Ergebnisse sind schnell messbar</li><li>A/B-Splittests für Betreffzeilen und Werbemittel</li></ul>
<h2>Was wir nicht bewerben</h2><p>Wir nehmen keine Werbung für bestimmte Branchen an, zum Beispiel Datingportale, alkoholische Getränke oder Astrologie-Angebote.</p></div></section>
<section class="alt"><div class="wrap prose"><h2>Häufige Fragen</h2>
<h3>Kostet die Erstberatung etwas?</h3><p>Nein, das erste Beratungsgespräch ist kostenlos.</p>
<h3>Was benötigen Sie von mir?</h3><p>Ein Werbemittel (Text- und HTML-Version) sowie eine Betreffzeile.</p>
<h3>Wie wird abgerechnet?</h3><p>In der Regel per Tausend-Kontakt-Preis (TKP). Auch eine Provision pro Lead oder Verkauf ist möglich.</p></div></section>{CTA}""",
hero=phero("Über uns", "BlueStar Direct Marketing GmbH – Ihr Partner für E-Mail-Marketing."))

pages["leistungen.html"] = page("leistungen.html", "Leistungen", "E-Mail-Marketing, Lead- und Adressgenerierung, Beratung und Reporting.",
f"""<section><div class="wrap"><p class="lead">Kundenzufriedenheit und eine vertrauensvolle, langfristige Partnerschaft stehen bei uns im Vordergrund. Individuelle Lösungen sind für uns selbstverständlich.</p>
<h2 style="margin-top:32px">Kernkompetenzen</h2>
{cards([("mail","E-Mail-Marketing","Unser Spezialgebiet: Newsletter-Kampagnen, die Zielgruppen ansprechen und Umsätze steigern."),
("target","Lead- und Adressgenerierung","Auf Wunsch gewinnen wir Leads und Adressen über ein Netzwerk reichweitenstarker Content-Webseiten.")])}</div></section>
<section class="alt"><div class="wrap"><h2>Direkte und persönliche Ansprache</h2>
<ul class="prose"><li>Auswahl der Zielgruppe nach Ihren Vorgaben oder mit unseren Tools</li><li>Beratung – die Entscheidung liegt bei Ihnen</li><li>Unterstützung bei der Erstellung der Werbemittel</li><li>Prüfung der Zustellbarkeit</li><li>Kontrolle der Werbemittel auf gängige Spamfilter</li></ul>
<h2 style="margin-top:36px">Worauf wir Wert legen</h2><p class="lead">Partnerschaftliche Zusammenarbeit ist der Schlüssel zum gemeinsamen Erfolg – mit Flexibilität, Transparenz und Verlässlichkeit.</p>
{cards([("target","Effektiv und simpel","Effektive Lösungen für Ihr Direktmarketing."),("clock","Flexibel und schnell","Auch kurzfristige Aktionen sind möglich."),
("euro","Transparent und fair","Faire Preise, nachvollziehbare Abwicklung, Reporting."),("handshake","Starke Partnerschaften","Ein großes Netzwerk leistungsstarker Partner.")])}</div></section>{CTA}""",
hero=phero("Leistungen", "Von der Zielgruppenauswahl bis zum Reporting."))

pages["emailmarketing.html"] = page("emailmarketing.html", "E-Mail-Marketing", "Warum professionelles E-Mail-Marketing richtig ist: schnell, günstig, messbar.",
f"""<section><div class="wrap"><h2>Warum Sie mit professionellem E-Mail-Marketing richtig liegen</h2>
<p class="lead">Unser Team erfahrener Experten weiß, worauf es bei einer erfolgreichen Kampagne ankommt.</p>
{cards([("clock","Direkte Ergebnisse","Rund 90&nbsp;% des Kampagnenerfolgs zeigen sich innerhalb von 48 Stunden."),
("euro","Geringe Kosten","Deutlich günstiger als die meisten anderen Formate, besonders als Offline-Mailings."),
("doc","Ausführliche Inhalte","Ideal für detaillierte Informationen – anders als kurze Social-Media-Beiträge."),
("inbox","Dauerhaft verfügbar","E-Mails bleiben im Postfach und können auch Tage später gelesen werden."),
("devices","Auf allen Geräten","Empfang am PC, Tablet und Smartphone."),
("chart","Transparentes Reporting","Nach dem Versand erhalten Sie einen klaren Bericht mit Öffnungs- und Klickrate.")])}</div></section>{CTA}""",
hero=phero("E-Mail-Marketing", "Newsletter-Werbung, die schnell wirkt und messbar ist."))

pages["kontakt.html"] = page("kontakt.html", "Kontakt", "Kontaktieren Sie die BlueStar Direct Marketing GmbH in Dresden.",
"""<section><div class="wrap"><p class="lead">Interesse an einer Zusammenarbeit oder Fragen zu unseren Leistungen? Wir melden uns zeitnah.</p>
<form action="send.php" method="post">
<div><label for="n">Name</label><input id="n" name="name" required autocomplete="name"></div>
<div><label for="e">E-Mail</label><input id="e" name="email" type="email" required autocomplete="email"></div>
<div><label for="m">Nachricht</label><textarea id="m" name="message" rows="6" required></textarea></div>
<input class="hp" name="website" tabindex="-1" autocomplete="off" aria-hidden="true">
<div><label><input type="checkbox" name="privacy" required style="width:auto"> Ich habe die <a href="datenschutz.html">Datenschutzerklärung</a> gelesen.</label></div>
<button class="btn primary" type="submit">Nachricht senden</button></form>
<p style="margin-top:32px"><strong>BlueStar Direct Marketing GmbH</strong><br>Altmarkt 10 B, 01067 Dresden<br>Tel. <a href="tel:+4935121789109">+49 351 21789109</a><br><a href="mailto:hallo@bluestar.direct">hallo@bluestar.direct</a></p></div></section>""",
hero=phero("Was können wir für Sie tun?", "Schreiben Sie uns – wir antworten schnell."))

pages["impressum.html"] = page("impressum.html", "Impressum", "Impressum der BlueStar Direct Marketing GmbH.",
"""<section><div class="wrap prose"><h1>Impressum</h1>
<p>BlueStar Direct Marketing GmbH<br>Altmarkt 10 B<br>01067 Dresden</p>
<p>Geschäftsführer: Marlon Ziebertz<br>Handelsregister: Amtsgericht Dresden, HRB 42941<br>USt-IdNr.: DE354234505</p>
<p>Kontakt: <a href="mailto:hallo@bluestar.direct">hallo@bluestar.direct</a>, Tel. +49 351 21789109</p>
<p><strong>TODO:</strong> Haftungsausschluss, Urheberrecht und Bildnachweise (Fotolia / stock.adobe.com) bitte wörtlich aus dem bisherigen Impressum übernehmen.</p></div></section>""")

pages["datenschutz.html"] = page("datenschutz.html", "Datenschutz", "Datenschutzerklärung der BlueStar Direct Marketing GmbH.",
"""<section><div class="wrap prose"><h1>Datenschutzerklärung</h1>
<p><strong>TODO:</strong> Bitte den Text der bisherigen Datenschutzerklärung übernehmen und anpassen: Die neue Seite nutzt kein WordPress, keine Cookies, keine externen Schriftarten und kein Tracking. Das Kontaktformular (send.php) verarbeitet Name, E-Mail und Nachricht und versendet sie per E-Mail.</p></div></section>""")

if __name__ == "__main__":
    for name, html in pages.items():
        (OUT / name).write_text(html, encoding="utf-8")
    print(f"{len(pages)} Seiten nach {OUT} geschrieben")
