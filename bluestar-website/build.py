#!/usr/bin/env python3
"""Baut die statische BlueStar-Direct-Seite nach dist/ (kein CMS, keine Datenbank)."""
from pathlib import Path

OUT = Path(__file__).parent / "dist"
YEAR = 2026
NAV = [("index.html", "Home"), ("ueber-uns.html", "Über uns"), ("leistungen.html", "Leistungen"),
       ("emailmarketing.html", "E-Mail-Marketing"), ("kontakt.html", "Kontakt")]

ICONS = {
    "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4"/>',
    "flow": '<path d="M4 6h8v6h8M4 18h8v-6"/>',
    "up": '<path d="M3 17l6-6 4 4 8-8M15 7h6v6"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
    "shield": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M9 12l2 2 4-4"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "euro": '<path d="M17 6a6 6 0 100 12M4 10h9M4 14h9"/>',
    "chart": '<path d="M4 20V10M10 20V4M16 20v-8M22 20H2"/>',
    "devices": '<rect x="2" y="5" width="14" height="10" rx="1"/><rect x="18" y="8" width="4" height="9" rx="1"/>',
    "inbox": '<path d="M3 13l3-8h12l3 8v6H3zM3 13h5l1 3h6l1-3h5"/>',
    "doc": '<path d="M6 3h9l4 4v14H6zM9 12h7M9 16h7"/>',
    "handshake": '<path d="M2 12l5-5 4 3 4-3 5 5-9 8z"/>',
}

def ico(name):
    return (f'<div class="ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg></div>')

def tile(i, t, p, cls=""):
    return f'<div class="tile rv {cls}">{ico(i)}<h3>{t}</h3><p>{p}</p></div>'

def photos(items):
    return '<div class="photos">' + "".join(
        f'<figure class="photo rv"><img src="assets/{img}" alt="{alt}" width="424" height="283" loading="lazy">'
        f'<figcaption><h3>{t}</h3><p>{p}</p></figcaption></figure>' for img, alt, t, p in items) + "</div>"

def head(eyebrow, h, lead="", center=False):
    return (f'<div class="head rv{" center" if center else ""}"><span class="eyebrow">{eyebrow}</span><h2>{h}</h2>'
            + (f'<p class="lead">{lead}</p>' if lead else "") + "</div>")

def split(img, alt, eyebrow, h, body, flip=False):
    return (f'<section><div class="wrap split{" flip" if flip else ""}"><div class="pic rv"><img src="assets/{img}" alt="{alt}" '
            f'width="424" height="283" loading="lazy"></div><div class="rv"><span class="eyebrow">{eyebrow}</span><h2>{h}</h2>{body}</div></div></section>')

def checks(items):
    return '<ul class="checks">' + "".join(f"<li>{i}</li>" for i in items) + "</ul>"

def faq(items):
    return '<div class="faq rv">' + "".join(f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in items) + "</div>"

def steps(items):
    return '<div class="steps">' + "".join(f'<div class="step rv"><h3>{t}</h3><p>{p}</p></div>' for t, p in items) + "</div>"

CTA = """<div class="cta rv"><span class="eyebrow" style="color:#9fd0ff">Unverbindlich &amp; kostenlos</span>
<h2>Bereit für Ihre nächste Kampagne?</h2><p class="lead">Das erste Beratungsgespräch ist kostenlos. Wir erstellen Ihnen gern ein individuelles Angebot.</p>
<div class="btns"><a class="btn light" href="kontakt.html">Angebot anfragen →</a></div></div>"""

def page(fname, title, desc, body, hero):
    nav = "".join(f'<li><a href="{h}"{" aria-current=page" if h == fname else ""}>{n}</a></li>' for h, n in NAV)
    return f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} – BlueStar Direct</title><meta name="description" content="{desc}">
<link rel="icon" href="assets/cropped-fav-192x192.png"><link rel="stylesheet" href="assets/style.css">
<script>document.documentElement.classList.add('js')</script></head><body>
<a class="skip" href="#main">Zum Inhalt springen</a>
<header class="site"><div class="wrap"><a class="logo" href="index.html"><img src="assets/logo-1.png" alt="BlueStar Direct" width="500" height="169"></a>
<button class="burger" aria-expanded="false" aria-controls="nav" onclick="var n=document.getElementById('nav');n.classList.toggle('open');this.setAttribute('aria-expanded',n.classList.contains('open'))">Menü</button>
<nav id="nav" aria-label="Hauptmenü"><ul>{nav}</ul></nav></div></header>
<main id="main">{hero}{body}</main>
<footer class="site"><div class="wrap"><div class="fgrid">
<div><strong style="color:#fff">BlueStar Direct Marketing GmbH</strong><br>Altmarkt 10 B<br>01067 Dresden</div>
<div><h4>Seiten</h4><ul>{"".join(f'<li><a href="{h}">{n}</a></li>' for h, n in NAV)}</ul></div>
<div><h4>Rechtliches</h4><ul><li><a href="impressum.html">Impressum</a></li><li><a href="datenschutz.html">Datenschutz</a></li><li><a href="assets/bluestar_agb_2022_agb_e-mail-kampagnen.pdf">AGB (PDF)</a></li></ul>
<h4 style="margin-top:22px">Kontakt</h4><ul><li><a href="mailto:hallo@bluestar.direct">hallo@bluestar.direct</a></li><li><a href="tel:+4935121789109">+49 351 21789109</a></li></ul></div></div>
<div class="copy">© {YEAR} BlueStar Direct Marketing GmbH</div></div></footer>
<script>var io='IntersectionObserver' in window&&new IntersectionObserver(function(e){{e.forEach(function(x){{if(x.isIntersecting){{x.target.classList.add('in');io.unobserve(x.target)}}}})}},{{threshold:.12}});document.querySelectorAll('.rv').forEach(function(el){{io?io.observe(el):el.classList.add('in')}})</script>
</body></html>"""

def pagehero(eyebrow, h, lead):
    return f'<div class="pagehero"><div class="wrap"><span class="eyebrow">{eyebrow}</span><h1>{h}</h1><p class="lead">{lead}</p></div></div>'

pages = {}

REPORT = """<svg viewBox="0 0 220 90" role="img" aria-label="Beispielgrafik eines Kampagnen-Reports"><defs><linearGradient id="g" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#46b4f0" stop-opacity=".5"/><stop offset="1" stop-color="#46b4f0" stop-opacity="0"/></linearGradient></defs>
<path d="M0 70 C25 66 35 40 60 44 S100 70 125 40 S175 10 220 16 V90 H0Z" fill="url(#g)"/>
<path d="M0 70 C25 66 35 40 60 44 S100 70 125 40 S175 10 220 16" fill="none" stroke="#2447d6" stroke-width="3" stroke-linecap="round"/>
<g fill="#2447d6" opacity=".85"><rect x="6" y="74" width="12" height="12" rx="3" opacity=".3"/><rect x="26" y="66" width="12" height="20" rx="3" opacity=".4"/><rect x="46" y="58" width="12" height="28" rx="3" opacity=".5"/><rect x="66" y="50" width="12" height="36" rx="3" opacity=".6"/></g></svg>"""

pages["index.html"] = page("index.html", "E-Mail-Marketing aus Dresden", "E-Mail-Marketing aus Dresden: Zielgruppen erreichen, Leads gewinnen, Umsatz steigern.",
f"""<div class="wrap"><div class="stats rv">
<div class="stat"><strong>90&nbsp;%</strong><span>des Kampagnenerfolgs innerhalb von 48&nbsp;Stunden</span></div>
<div class="stat"><strong>DACH</strong><span>Interessenten in Deutschland, Österreich &amp; Schweiz</span></div>
<div class="stat"><strong>100&nbsp;%</strong><span>Double-Opt-In bestätigte Empfänger</span></div>
<div class="stat"><strong>0&nbsp;€</strong><span>für das erste Beratungsgespräch</span></div></div></div>
<section><div class="wrap">{head("Unser Ansatz","Online-Marketing, das ankommt","Wir verbinden die richtige Zielgruppe mit schlanken Abläufen und messbaren Ergebnissen.")}
<div class="bento">
{tile("target","Optimale Zielgruppenansprache","Ihre Botschaft erreicht genau die Menschen, die sich dafür interessieren – ausgewählt nach Alter, Wohnort und Interessen.","w3")}
{tile("flow","Smarte und effiziente Workflows","Schlanke Abläufe von der Planung über den Versand bis zum Reporting.","w3")}
{tile("up","Sales und Leads steigern","Messbare Ergebnisse statt Streuverluste.","dark w4")}
{tile("shield","Rechtssicher","Wir halten die gesetzlichen Vorgaben ein.")}</div></div></section>
<section class="ice"><div class="wrap">{head("Ihr Nutzen","Erfolgreiches E-Mail-Marketing mit der BlueStar Direct Marketing GmbH","Wir setzen auf Qualität statt auf günstige Anbieter aus dem Ausland mit riesigen, unsauberen Datenbanken.")}
{photos([("trends.jpg","Auswertung von Kampagnendaten","Analysen und Trends","Wir werten Kampagnen aus und leiten Empfehlungen ab."),
("umsatz.jpg","Handschlag nach Geschäftsabschluss","Mehr Umsatz","Direkte Ansprache, die Verkäufe auslöst."),
("neukunden.jpg","Lächelnde Frau mit Smartphone","Neue Kunden","Neue Interessenten in der DACH-Region erreichen."),
("produkt.jpg","Einkaufswagen mit Paketen vor einem Laptop","Produkte einführen","Neue Produkte gezielt im Markt platzieren.")])}</div></section>
<section><div class="wrap">{head("So arbeiten wir","In fünf Schritten zur Kampagne","",True)}
{steps([("Zielgruppe","Auswahl nach Ihren Vorgaben oder mit unseren Tools."),("Werbemittel","Wir unterstützen bei Text- und HTML-Version."),("Prüfung","Zustellbarkeit und Spamfilter-Check."),("Versand","Schnell, auch kurzfristig möglich."),("Report","Öffnungs- und Klickrate transparent aufbereitet.")])}</div></section>
<section class="ice"><div class="wrap split"><div class="rv"><span class="eyebrow">Weshalb BlueStar Direct</span><h2>Qualität statt Masse</h2>
<p class="lead" style="margin-top:18px">Sämtliche Empfänger haben ihre Anmeldung per Double-Opt-In bestätigt. Das schützt Ihre Reputation und steigert die Wirkung.</p>
{checks(["Großer, gepflegter Empfängerpool","Rechtssichere Abwicklung nach gesetzlichen Vorgaben","Feste Ansprechpartner und individuelle Lösungen"])}</div>
<div class="pic rv"><img src="assets/top3.jpg" alt="Junge Frau freut sich über eine Nachricht auf dem Smartphone" width="1080" height="350" loading="lazy"></div></div></section>
{CTA}""",
hero=f"""<div class="hero"><div class="wrap herogrid"><div class="rv"><span class="eyebrow">E-Mail-Marketing · Dresden</span>
<h1>Ihre Botschaft. <span class="mark">Direkt</span> im Postfach.</h1>
<p class="lead">Willkommen bei BlueStar Direct: Wir bringen Ihre Angebote per Newsletter zu den Menschen, die sich dafür interessieren – persönlich, transparent und messbar.</p>
<div class="btns"><a class="btn primary" href="kontakt.html">Angebot anfragen →</a><a class="btn ghost" href="leistungen.html">Unsere Leistungen</a></div>
<div class="trust"><span>Double-Opt-In</span><span>DACH-Region</span><span>Persönliche Beratung</span></div></div>
<div class="collage rv"><img class="p p1" src="assets/umsatz.jpg" alt="Handschlag nach Geschäftsabschluss" width="424" height="283">
<img class="p p2" src="assets/neukunden.jpg" alt="Lächelnde Frau mit Smartphone" width="424" height="283">
<div class="report"><b>Kampagnen-Report</b><small>Öffnungen · Klicks · Conversions</small>{REPORT}</div></div></div></div>""")

pages["ueber-uns.html"] = page("ueber-uns.html", "Über uns", "Die BlueStar Direct Marketing GmbH – E-Mail-Marketing-Agentur in Dresden.",
f"""{split("neukunden.jpg","Lächelnde Frau mit Smartphone","Unsere Datenbank","Eine Datenbank, viele Möglichkeiten",
'<p class="lead" style="margin-top:18px">Wir verfügen über eine große Datenbank an Interessenten in Deutschland, der Schweiz und Österreich. Empfänger lassen sich gezielt auswählen – zum Beispiel nach:</p>'+checks(["Alter","Wohnort","Produktinteressen"]))}
<section class="ice"><div class="wrap">{head("Vorteile","Warum E-Mail-Marketing?")}
<div class="bento">{tile("devices","Auf allen Endgeräten","Funktioniert am PC, Tablet und Smartphone.")}{tile("mail","Direkter Draht","Erreicht Empfänger unmittelbar im Postfach.")}{tile("chart","Schnell messbar","Ergebnisse liegen rasch vor – inklusive A/B-Splittests für Betreffzeilen und Werbemittel.")}</div></div></section>
<section><div class="wrap split"><div class="rv"><span class="eyebrow">Unsere Grundsätze</span><h2>Was wir nicht bewerben</h2>
<p class="lead" style="margin-top:18px">Seriosität ist uns wichtig. Wir nehmen keine Werbung für bestimmte Branchen an, zum Beispiel Datingportale, alkoholische Getränke oder Astrologie-Angebote.</p></div>
<div class="tile dark rv">{ico("shield")}<h3>Saubere Kampagnen</h3><p>Das schützt Ihre Marke, die Empfänger und unsere gemeinsame Reputation.</p></div></div></section>
<section class="ice"><div class="wrap">{head("FAQ","Häufige Fragen","",True)}
{faq([("Kostet die Erstberatung etwas?","Nein, das erste Beratungsgespräch ist kostenlos."),
("Was benötigen Sie von mir?","Ein Werbemittel (Text- und HTML-Version) sowie eine Betreffzeile."),
("Wie wird abgerechnet?","In der Regel per Tausend-Kontakt-Preis (TKP). Auch eine Provision pro Lead oder Verkauf ist möglich.")])}</div></section>{CTA}""",
hero=pagehero("Über uns","BlueStar Direct Marketing GmbH","Ihre E-Mail-Marketing-Agentur aus Dresden."))

pages["leistungen.html"] = page("leistungen.html", "Leistungen", "E-Mail-Marketing, Lead- und Adressgenerierung, Beratung und Reporting.",
f"""<section><div class="wrap">{head("Kernkompetenzen","Das machen wir für Sie","Kundenzufriedenheit und eine vertrauensvolle, langfristige Partnerschaft stehen im Vordergrund. Individuelle Lösungen sind für uns selbstverständlich.")}
<div class="bento">{tile("mail","E-Mail-Marketing","Unser Spezialgebiet: Newsletter-Kampagnen, die Zielgruppen ansprechen und Umsätze steigern.","w3")}
{tile("target","Lead- und Adressgenerierung","Auf Wunsch gewinnen wir Leads und Adressen über ein Netzwerk reichweitenstarker Content-Webseiten, die ihren Besuchern einen Mehrwert bieten.","w3 dark")}</div></div></section>
{split("trends.jpg","Auswertung von Kampagnendaten","Ablauf","Direkte und persönliche Ansprache: E-Mail für Sie",
'<p class="lead" style="margin-top:18px">Wir beraten – die Entscheidung liegt bei Ihnen.</p>'+checks(["Auswahl der Zielgruppe nach Ihren Vorgaben oder mit unseren Tools","Unterstützung bei der Erstellung der Werbemittel","Prüfung der Zustellbarkeit","Kontrolle der Werbemittel auf gängige Spamfilter"]),True)}
<section class="ice"><div class="wrap">{head("Unsere Werte","Worauf wir Wert legen","Partnerschaftliche Zusammenarbeit ist der Schlüssel zum gemeinsamen Erfolg – mit Flexibilität, Transparenz und Verlässlichkeit.")}
<div class="bento">{tile("target","Effektiv und simpel","Effektive Lösungen für Ihr Direktmarketing, die Ihr Ziel erreichen.","w3")}{tile("clock","Flexibel und schnell","Auch kurzfristige Aktionen und Werbekampagnen sind möglich.","w3")}
{tile("euro","Transparent und fair","Faire Preise, nachvollziehbare Auftragsabwicklung und Reporting.","w3")}{tile("handshake","Starke Partnerschaften","Ein großes Netzwerk leistungsstarker Partner ermöglicht vielseitige Lösungen.","w3")}</div></div></section>{CTA}""",
hero=pagehero("Leistungen","Von der Zielgruppe bis zum Report","Alles aus einer Hand – persönlich betreut."))

pages["emailmarketing.html"] = page("emailmarketing.html", "E-Mail-Marketing", "Warum professionelles E-Mail-Marketing richtig ist: schnell, günstig, messbar.",
f"""<section><div class="wrap">{head("Sechs gute Gründe","Warum Sie mit professionellem E-Mail-Marketing richtig liegen","Unser Team erfahrener Experten weiß, worauf es bei einer erfolgreichen Kampagne ankommt.")}
<div class="bento">
<div class="tile dark rv w3"><div class="num">90&nbsp;%</div><h3>Direkte Ergebnisse</h3><p>Rund 90&nbsp;% des Kampagnenerfolgs zeigen sich innerhalb von 48 Stunden.</p></div>
{tile("euro","Geringe Kosten","Deutlich günstiger als die meisten anderen Formate, besonders als Offline-Mailings.","w3")}
{tile("doc","Ausführliche Inhalte","Ideal für detaillierte Informationen – anders als kurze Social-Media-Beiträge.")}
{tile("inbox","Dauerhaft verfügbar","E-Mails bleiben im Postfach und können auch Tage später gelesen werden.")}
{tile("devices","Auf allen Geräten","Empfang am PC, Tablet und Smartphone.")}</div></div></section>
{split("produkt.jpg","Einkaufswagen mit Paketen vor einem Laptop","Transparenz","Messbar bis zum letzten Klick",
'<p class="lead" style="margin-top:18px">Nach dem Versand erhalten Sie einen klaren Report mit Kennzahlen wie Öffnungs- und Klickrate.</p>'+checks(["Öffnungsrate","Klickrate","Nachvollziehbare Auswertung"]),True)}{CTA}""",
hero=pagehero("E-Mail-Marketing","Newsletter-Werbung, die wirkt","Schnell, günstig und messbar – Ihre Botschaft kommt an."))

pages["kontakt.html"] = page("kontakt.html", "Kontakt", "Kontaktieren Sie die BlueStar Direct Marketing GmbH in Dresden.",
"""<section><div class="wrap contact"><form action="send.php" method="post" class="rv">
<div><label for="n">Name</label><input id="n" name="name" required autocomplete="name"></div>
<div><label for="e">E-Mail</label><input id="e" name="email" type="email" required autocomplete="email"></div>
<div><label for="m">Nachricht</label><textarea id="m" name="message" rows="7" required></textarea></div>
<input class="hp" name="website" tabindex="-1" autocomplete="off" aria-hidden="true">
<div><label style="font-weight:400"><input type="checkbox" name="privacy" required>Ich habe die <a href="datenschutz.html">Datenschutzerklärung</a> gelesen.</label></div>
<div><button class="btn primary" type="submit">Nachricht senden →</button></div></form>
<aside class="infobox rv"><h3>BlueStar Direct Marketing GmbH</h3><p>Altmarkt 10 B<br>01067 Dresden</p>
<p>Tel. <a href="tel:+4935121789109">+49 351 21789109</a><br><a href="mailto:hallo@bluestar.direct">hallo@bluestar.direct</a></p>
<p style="margin:0;color:#c9d6ff">Das erste Beratungsgespräch ist kostenlos.</p></aside></div></section>""",
hero=pagehero("Kontakt","Was können wir für Sie tun?","Interesse an einer Zusammenarbeit oder Fragen zu unseren Leistungen? Wir melden uns zeitnah."))

pages["impressum.html"] = page("impressum.html", "Impressum", "Impressum der BlueStar Direct Marketing GmbH.",
"""<section><div class="wrap prose">
<p>BlueStar Direct Marketing GmbH<br>Altmarkt 10 B<br>01067 Dresden</p>
<p>Geschäftsführer: Marlon Ziebertz<br>Handelsregister: Amtsgericht Dresden, HRB 42941<br>USt-IdNr.: DE354234505</p>
<p>Kontakt: <a href="mailto:hallo@bluestar.direct">hallo@bluestar.direct</a>, Tel. +49 351 21789109</p>
<p><strong>TODO:</strong> Haftungsausschluss, Urheberrecht und Bildnachweise (Fotolia / stock.adobe.com) bitte wörtlich aus dem bisherigen Impressum übernehmen.</p></div></section>""",
hero=pagehero("Rechtliches","Impressum",""))

pages["datenschutz.html"] = page("datenschutz.html", "Datenschutz", "Datenschutzerklärung der BlueStar Direct Marketing GmbH.",
"""<section><div class="wrap prose">
<p><strong>TODO:</strong> Bitte den Text der bisherigen Datenschutzerklärung übernehmen und anpassen: Die neue Seite nutzt kein WordPress, keine Cookies, keine externen Schriftarten und kein Tracking. Das Kontaktformular (send.php) verarbeitet Name, E-Mail und Nachricht und versendet sie per E-Mail.</p></div></section>""",
hero=pagehero("Rechtliches","Datenschutzerklärung",""))

if __name__ == "__main__":
    for name, html in pages.items():
        (OUT / name).write_text(html, encoding="utf-8")
    print(f"{len(pages)} Seiten nach {OUT} geschrieben")
