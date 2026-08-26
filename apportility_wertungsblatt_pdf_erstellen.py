#!/usr/bin/env python3
"""Generate a fillable (AcroForm) PDF version of the Apportility Wertungsblatt.

Uses the two supplied illustrations as full-page backgrounds and overlays
real PDF form fields (fillable on iPhone/iPad in Files/Preview/Safari/etc.)
on every blank in the design.
"""
import os
import tempfile
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "assets")
OUT_PDF = os.path.join(BASE_DIR, "Apportility_Wertungsblatt_ausfuellbar.pdf")


def _as_jpeg(src_png, quality=92):
    """Re-encode the background PNG as JPEG to keep the PDF file small."""
    dst = os.path.join(tempfile.gettempdir(), os.path.basename(src_png).replace(".png", ".jpg"))
    Image.open(src_png).convert("RGB").save(dst, "JPEG", quality=quality, optimize=True)
    return dst


PAGE1_IMG = _as_jpeg(os.path.join(SRC_DIR, "wertungsblatt_seite1.png"))
PAGE2_IMG = _as_jpeg(os.path.join(SRC_DIR, "wertungsblatt_seite2.png"))

IMG_W, IMG_H = 1055, 1491
S = 595.28 / IMG_W          # px -> pt scale factor
PAGE_W, PAGE_H = IMG_W * S, IMG_H * S

TRANSPARENT = Color(1, 1, 1, alpha=0)
TEXT_COLOR = Color(0.20, 0.25, 0.08)  # dark olive, matches design ink


def px(x0, y0, x1, y1):
    """Convert an image-pixel rect (top-left, bottom-right) to a reportlab
    (x, y, width, height) rect in points, with y measured from the bottom."""
    pdf_x0 = x0 * S
    pdf_x1 = x1 * S
    pdf_y0 = PAGE_H - y1 * S
    pdf_y1 = PAGE_H - y0 * S
    return pdf_x0, pdf_y0, pdf_x1 - pdf_x0, pdf_y1 - pdf_y0


def add_field(c, name, rect, font_size=9, multiline=False, value=""):
    x, y, w, h = rect
    c.acroForm.textfield(
        name=name,
        tooltip=name,
        x=x, y=y, width=w, height=h,
        value=value,
        borderStyle="underlined",
        borderWidth=0,
        borderColor=TRANSPARENT,
        fillColor=TRANSPARENT,
        textColor=TEXT_COLOR,
        forceBorder=False,
        fontSize=font_size,
        maxlen=1000 if multiline else 60,
        fieldFlags="multiline" if multiline else "doNotScroll",
    )


def score_grid_fields(c, page_prefix, row_centers, col_groups, row_h=40):
    """8 category rows x 2 parcours x (DG1, DG2, DG3, SUMME)."""
    for r_idx, y_center in enumerate(row_centers, start=1):
        y0, y1 = y_center - row_h / 2, y_center + row_h / 2
        for group_name, cols in col_groups.items():
            for col_name, (cx0, cx1) in cols.items():
                fname = f"{page_prefix}_row{r_idx}_{group_name}_{col_name}"
                rect = px(cx0, y0, cx1, y1)
                add_field(c, fname, rect, font_size=10)


def build():
    c = canvas.Canvas(OUT_PDF, pagesize=(PAGE_W, PAGE_H))
    c.setTitle("Apportility Wertungsblatt (ausfüllbar)")
    c.acroForm.extras["NeedAppearances"] = "true"

    # Column layout shared by both pages
    p1_cols = {
        "DG1": (302, 355), "DG2": (355, 410), "DG3": (410, 465), "SUMME": (465, 525),
    }
    p2_cols = {
        "DG1": (528, 583), "DG2": (583, 638), "DG3": (638, 693), "SUMME": (693, 758),
    }

    # ---------------- PAGE 1 ----------------
    c.drawImage(PAGE1_IMG, 0, 0, width=PAGE_W, height=PAGE_H)

    # Teilnehmer-Info
    add_field(c, "datum", px(140, 460, 290, 480))
    add_field(c, "hundefuehrer", px(232, 496, 490, 516))
    add_field(c, "hund", px(138, 533, 450, 553))
    add_field(c, "team_name", px(198, 571, 430, 591))

    add_field(c, "ort", px(567, 490, 745, 510), value="Koksijde")
    add_field(c, "klasse", px(598, 533, 745, 553))
    add_field(c, "startnummer", px(647, 571, 745, 591))

    row_centers_p1 = [723, 774, 825, 876, 927, 978, 1029, 1080]
    score_grid_fields(c, "s1", row_centers_p1,
                       {"parcours1": p1_cols, "parcours2": p2_cols}, row_h=42)

    # Zwischensumme Seite 1
    add_field(c, "s1_zwischensumme_parcours1", px(465, 1103, 525, 1150), font_size=11)
    add_field(c, "s1_zwischensumme_parcours2", px(693, 1103, 758, 1150), font_size=11)

    # Kurze Notizen
    add_field(c, "s1_notizen", px(50, 1232, 605, 1418), multiline=True, font_size=9)

    c.showPage()

    # ---------------- PAGE 2 ----------------
    c.drawImage(PAGE2_IMG, 0, 0, width=PAGE_W, height=PAGE_H)

    row_centers_p2 = [555, 614, 673, 732, 791, 850, 909, 968]
    score_grid_fields(c, "s2", row_centers_p2,
                       {"parcours3": p1_cols, "parcours4": p2_cols}, row_h=48)

    # Zwischensumme Seite 2
    add_field(c, "s2_zwischensumme_parcours3", px(465, 985, 525, 1040), font_size=11)
    add_field(c, "s2_zwischensumme_parcours4", px(693, 985, 758, 1040), font_size=11)

    # Gesamtübersicht
    overview_rows = [
        "gesamt_parcours1", "gesamt_parcours2", "gesamt_parcours3", "gesamt_parcours4",
        "bonus_gesamt", "strafpunkte", "endergebnis", "platzierung",
    ]
    overview_centers = [1168, 1201, 1234, 1267, 1300, 1333, 1366, 1399]
    for name, y_center in zip(overview_rows, overview_centers):
        rect = px(195, y_center - 12, 290, y_center + 12)
        add_field(c, name, rect, font_size=10)

    # Besondere Notizen
    add_field(c, "s2_notizen", px(325, 1150, 715, 1415), multiline=True, font_size=9)

    c.showPage()
    c.save()
    print("wrote", OUT_PDF)


if __name__ == "__main__":
    build()
