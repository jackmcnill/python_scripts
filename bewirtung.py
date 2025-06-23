import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Funktion zum Zeichnen einer Tabelle mit Rahmen
def draw_table(c, data, x, y, col_widths, row_height):
    num_rows = len(data)
    num_cols = len(data[0])

    for row in range(num_rows):
        for col in range(num_cols):
            cell_x = x + sum(col_widths[:col])
            cell_y = y - (row * row_height)
            c.rect(cell_x, cell_y - row_height, col_widths[col], row_height, stroke=1, fill=0)
            text = str(data[row][col])
            c.drawString(cell_x + 5, cell_y - row_height + 5, text)

# Funktion zur Erstellung des PDF-Bewirtungsbelegs
def erstelle_bewirtungsbeleg(dateiname, bewirtende_person, bewirtete_personen, ort_der_bewirtung, datum, anlass, aufwendungen_rechnung, trinkgeld, ort_datum):
    c = canvas.Canvas(dateiname, pagesize=letter)
    c.setFont("Helvetica", 12)

    # Titel
    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, 750, "Bewirtungsbeleg")
    c.setFont("Helvetica", 12)

    # Allgemeine Informationen (eine gemeinsame Tabelle)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 720, "Allgemeine Informationen")

    bewirtete_personen_str = ", ".join(bewirtete_personen)

    info_data = [
        ["Tag der Bewirtung:", datum.strftime('%d.%m.%Y')],
        ["Ort der Bewirtung:", ort_der_bewirtung],
        ["Bewirtende Person:", bewirtende_person],
        ["Bewirtete Personen:", bewirtete_personen_str],
        ["Anlass der Bewirtung:", anlass]
    ]
    draw_table(c, info_data, 50, 700, [160, 340], 20)

    # Kostenaufstellung
    y_pos = 700 - len(info_data) * 20 - 40
    c.drawString(50, y_pos, "Kostenaufstellung:")
    y_pos -= 20

    kosten_data = [
        ["Aufwendungen gemäß Rechnung:", f"{aufwendungen_rechnung:.2f} EUR"],
        ["Trinkgeld:", f"{trinkgeld:.2f} EUR"],
        ["Gesamtbetrag:", f"{(aufwendungen_rechnung + trinkgeld):.2f} EUR"]
    ]
    draw_table(c, kosten_data, 50, y_pos, [250, 150], 20)
    y_pos -= len(kosten_data) * 20 + 40

    # Ort, Datum & Unterschrift
    c.drawString(50, y_pos, f"Ort, Datum: {ort_datum}")
    c.drawString(350, y_pos, "Unterschrift:")

    c.save()
    messagebox.showinfo("Erfolg", f"Bewirtungsbeleg wurde erfolgreich erstellt: {dateiname}")

# Funktion zum Verarbeiten der Eingaben und Erstellen des Belegs
def on_submit():
    bewirtende_person = entry_bewirtende_person.get()
    ort_der_bewirtung = entry_ort_der_bewirtung.get()
    datum_input = entry_datum.get()
    anlass = entry_anlass.get()
    bewirtete_personen_input = entry_bewirtete_personen.get()
    ort_datum = entry_ort_datum.get()

    bewirtete_personen = [person.strip() for person in bewirtete_personen_input.split(",")]

    try:
        datum = datetime.strptime(datum_input, "%d.%m.%Y")
    except ValueError:
        messagebox.showerror("Fehler", "Bitte ein gültiges Datum im Format TT.MM.JJJJ eingeben.")
        return
    
    try:
        aufwendungen_rechnung = float(entry_aufwendungen_rechnung.get())
        trinkgeld = float(entry_trinkgeld.get())
    except ValueError:
        messagebox.showerror("Fehler", "Die Beträge müssen gültige Zahlen sein.")
        return

    # Dateiname automatisch erzeugen
    jetzt = datetime.now()
    dateiname = f"bewirtungsbeleg_{jetzt.strftime('%Y%m%d_%H%M%S')}.pdf"

    # PDF erstellen
    erstelle_bewirtungsbeleg(
        dateiname,
        bewirtende_person,
        bewirtete_personen,
        ort_der_bewirtung,
        datum,
        anlass,
        aufwendungen_rechnung,
        trinkgeld,
        ort_datum
    )

# GUI erstellen
root = tk.Tk()
root.title("Bewirtungsbeleg Erstellen")

# Eingabefelder und Labels
labels_entries = [
    ("Tag der Bewirtung (TT.MM.JJJJ):", "entry_datum"),
    ("Ort der Bewirtung:", "entry_ort_der_bewirtung"),
    ("Bewirtende Person:", "entry_bewirtende_person"),
    ("Bewirtete Personen (durch Komma getrennt):", "entry_bewirtete_personen"),
    ("Anlass der Bewirtung:", "entry_anlass"),
    ("Aufwendungen gemäß Rechnung (EUR):", "entry_aufwendungen_rechnung"),
    ("Trinkgeld (EUR):", "entry_trinkgeld"),
    ("Ort, Datum:", "entry_ort_datum")
]

entries = {}

for i, (label_text, var_name) in enumerate(labels_entries):
    label = tk.Label(root, text=label_text)
    label.grid(row=i, column=0, padx=10, pady=5, sticky='e')
    entry = tk.Entry(root, width=40)
    entry.grid(row=i, column=1, padx=10, pady=5)
    entries[var_name] = entry

entry_datum = entries["entry_datum"]
entry_ort_der_bewirtung = entries["entry_ort_der_bewirtung"]
entry_bewirtende_person = entries["entry_bewirtende_person"]
entry_bewirtete_personen = entries["entry_bewirtete_personen"]
entry_anlass = entries["entry_anlass"]
entry_aufwendungen_rechnung = entries["entry_aufwendungen_rechnung"]
entry_trinkgeld = entries["entry_trinkgeld"]
entry_ort_datum = entries["entry_ort_datum"]

# Button zum Erstellen
submit_btn = tk.Button(root, text="Beleg erstellen", command=on_submit)
submit_btn.grid(row=len(labels_entries), column=0, columnspan=2, pady=20)

root.mainloop()
