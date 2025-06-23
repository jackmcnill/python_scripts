import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import csv
import os

# Hilfsfunktion zum Umbruch langer Texte
def wrap_text(text, max_length=60):
    """Teilt den Text in Zeilen auf, falls er länger als max_length ist."""
    lines = []
    while len(text) > max_length:
        split_at = text.rfind(' ', 0, max_length)
        if split_at == -1:  # Kein Leerzeichen gefunden, harte Trennung
            split_at = max_length
        lines.append(text[:split_at])
        text = text[split_at:].lstrip()
    lines.append(text)
    return '\n'.join(lines)

# GUI-Funktionen
def datei_oeffnen():
    global eingabe_datei, header_zeile
    dateipfad = filedialog.askopenfilename(filetypes=[('CSV- und Textdateien', '*.csv *.txt'),  # Beide Dateitypen gleichzeitig anzeigen
        ('CSV-Dateien', '*.csv'),                # Nur CSV-Dateien anzeigen
        ('Textdateien', '*.txt'),                # Nur Textdateien anzeigen
        ('Alle Dateien', '*.*')])
    if dateipfad:
        eingabe_datei = dateipfad
        eingabe_datei_entry.delete(0, tk.END)
        eingabe_datei_entry.insert(0, dateipfad)
        lade_header_zeile()
        zeige_vorschau()

def lade_header_zeile():
    global header_zeile
    try:
        trennzeichen = trennzeichen_combobox.get()
        if trennzeichen == "Tab":
            trennzeichen = "\t"
        with open(eingabe_datei, mode='r', encoding='utf-8') as eingabe:
            reader = csv.reader(eingabe, delimiter=trennzeichen)
            header_zeile = next(reader)
            spalten_combobox['values'] = header_zeile
            spalten_combobox.set(header_zeile[0])
            spalten_breite = 150
            preview_table['columns'] = header_zeile
            for spalte in header_zeile:
                preview_table.heading(spalte, text=spalte)
                preview_table.column(spalte, width=spalten_breite, anchor='w')
    except Exception as e:
        messagebox.showerror('Fehler', f'Fehler beim Lesen der Datei: {str(e)}')

def zeige_vorschau():
    trennzeichen = trennzeichen_combobox.get()
    if trennzeichen == "Tab":
        trennzeichen = "\t"
    try:
        for item in preview_table.get_children():
            preview_table.delete(item)

        spalten_breite = 150
        with open(eingabe_datei, mode='r', encoding='utf-8') as eingabe:
            reader = csv.reader(eingabe, delimiter=trennzeichen)
            header = next(reader)

            preview_table['columns'] = header
            for spalte in header:
                preview_table.heading(spalte, text=spalte)
                preview_table.column(spalte, width=spalten_breite, anchor='w', stretch=False)

            for i, zeile in enumerate(reader):
                if i < 10:
                    preview_table.insert("", tk.END, values=zeile)
                else:
                    break
    except Exception as e:
        messagebox.showerror('Fehler', f'Fehler beim Laden der Vorschau: {str(e)}')

def verarbeite_datei():
    try:
        trennzeichen = trennzeichen_combobox.get()
        if trennzeichen == "Tab":
            trennzeichen = "\t"
        spalte = spalten_combobox.get()
        datentyp = datentyp_var.get()

        if not eingabe_datei or not spalte or not datentyp:
            messagebox.showerror('Fehler', 'Bitte alle Felder ausfüllen!')
            return

        ausgabe_datei = eingabe_datei.replace('.csv', '_edit.csv')

        if datentyp == 'split_only':
            max_groesse_mb = int(teilgroesse_entry.get())
            teile_datei(eingabe_datei, max_groesse_mb=max_groesse_mb, loesche_original=False)
            return

        with open(eingabe_datei, mode='r', encoding='utf-8') as eingabe:
            reader = csv.reader(eingabe, delimiter=trennzeichen)
            header = next(reader)
            spalten_index = header.index(spalte)

            with open(ausgabe_datei, mode='w', encoding='utf-8', newline='') as ausgabe:
                writer = csv.writer(ausgabe, delimiter=';')

                if datentyp == 'md5':
                    writer.writerow(['c_md5id', 'c_email'])
                elif datentyp == 'sha256':
                    writer.writerow(['c_sha256id', 'c_email'])
                else:
                    writer.writerow(['c_email'])

                for zeile in reader:
                    wert = zeile[spalten_index].strip()
                    if wert:
                        if datentyp in ['md5', 'sha256']:
                            writer.writerow([wert, ""])
                        else:
                            writer.writerow([wert])

        teile_datei(ausgabe_datei, loesche_original=False)

    except Exception as e:
        messagebox.showerror('Fehler', str(e))

def teile_datei(dateipfad, max_groesse_mb=95, loesche_original=False):
    try:
        dateigroesse = os.path.getsize(dateipfad) / (1024 * 1024)
        if dateigroesse <= max_groesse_mb:
            status_text = f'Datei erfolgreich verarbeitet und gespeichert: {dateipfad}'
            status_label.config(text=wrap_text(status_text))
            return

        with open(dateipfad, mode='r', encoding='utf-8') as datei:
            reader = csv.reader(datei, delimiter=';')
            header = next(reader)

            teil_index = 1
            aktuelle_zeilen = []
            aktuelle_groesse = 0

            for zeile in reader:
                zeilengroesse = sum(len(str(e)) for e in zeile) + len(header) + 2
                aktuelle_zeilen.append(zeile)
                aktuelle_groesse += zeilengroesse

                if aktuelle_groesse > max_groesse_mb * 1024 * 1024:
                    teil_name = f"{dateipfad.replace('.csv', '')}_teil{teil_index}.csv"
                    with open(teil_name, mode='w', encoding='utf-8', newline='') as ausgabe:
                        writer = csv.writer(ausgabe, delimiter=';')
                        writer.writerow(header)
                        writer.writerows(aktuelle_zeilen)

                    teil_index += 1
                    aktuelle_zeilen = []
                    aktuelle_groesse = 0

            if aktuelle_zeilen:
                teil_name = f"{dateipfad.replace('.csv', '')}_teil{teil_index}.csv"
                with open(teil_name, mode='w', encoding='utf-8', newline='') as ausgabe:
                    writer = csv.writer(ausgabe, delimiter=';')
                    writer.writerow(header)
                    writer.writerows(aktuelle_zeilen)

        if loesche_original:
            os.remove(dateipfad)

        status_text = f'Datei wurde in {teil_index} Teile geteilt.'
        status_label.config(text=wrap_text(status_text))

    except Exception as e:
        status_label.config(text=f'Fehler beim Teilen der Datei: {str(e)}')

# GUI erstellen
root = tk.Tk()
root.title('Blacklist für ELAINE aufbereiten')
root.geometry('820x650')

datentyp_var = tk.StringVar(value='email')

# Eingabedatei auswählen
tk.Label(root, text='Eingabedatei:').grid(row=0, column=0, padx=5, pady=5)
eingabe_datei_entry = tk.Entry(root, width=50)
eingabe_datei_entry.grid(row=0, column=1, padx=5, pady=5)
tk.Button(root, text='Datei wählen', command=datei_oeffnen).grid(row=0, column=2, padx=5, pady=5)

# Vorschau-Frame
preview_frame = tk.Frame(root, width=800, height=300)
preview_frame.grid(row=1, column=0, columnspan=3, pady=5, sticky="n")

preview_table = ttk.Treeview(preview_frame, columns=[], show="headings", height=15)
preview_table.pack(side=tk.TOP, fill=tk.BOTH, expand=False)

preview_frame.grid_configure(sticky="ew")
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=1)

preview_table.configure(height=15)
preview_frame.pack_propagate(False)

preview_table['columns'] = ['Platzhalter']
preview_table.heading('Platzhalter', text='Platzhalter (Datei laden...)')
preview_table.column('Platzhalter', width=800, anchor='w', stretch=False)

# Vorschau aktualisieren
def zeige_vorschau():
    trennzeichen = trennzeichen_combobox.get()
    if trennzeichen == "Tab":
        trennzeichen = "\t"
    try:
        for item in preview_table.get_children():
            preview_table.delete(item)

        spalten_breite = 150
        with open(eingabe_datei, mode='r', encoding='utf-8') as eingabe:
            reader = csv.reader(eingabe, delimiter=trennzeichen)
            header = next(reader)

            preview_table['columns'] = header
            for spalte in header:
                preview_table.heading(spalte, text=spalte)
                preview_table.column(spalte, width=spalten_breite, anchor='w', stretch=False)

            for i, zeile in enumerate(reader):
                if i < 10:
                    preview_table.insert("", tk.END, values=zeile)
                else:
                    break
    except Exception as e:
        messagebox.showerror('Fehler', f'Fehler beim Laden der Vorschau: {str(e)}')

# Trennzeichen-Auswahl
tk.Label(root, text='Trennzeichen:').grid(row=2, column=0, padx=5, pady=5)
trennzeichen_combobox = ttk.Combobox(root, values=[';', ',', 'Tab'], state='readonly', width=5)
trennzeichen_combobox.set(';')
trennzeichen_combobox.grid(row=2, column=1, padx=5, pady=5)
#trennzeichen_combobox.bind('<<ComboboxSelected>>', lambda event: zeige_vorschau())
trennzeichen_combobox.bind('<<ComboboxSelected>>', lambda event: [lade_header_zeile(), zeige_vorschau()])

# Spalten-Auswahl
tk.Label(root, text='Spalten:').grid(row=3, column=0, padx=5, pady=5)
spalten_combobox = ttk.Combobox(root, state='readonly', width=40)
spalten_combobox.grid(row=3, column=1, padx=5, pady=5)

# Frame für Datentyp-Label und Radiobuttons
datentyp_container = tk.Frame(root)
datentyp_container.grid(row=4, column=0, columnspan=3, pady=5, sticky="ew")

# Label im Frame
tk.Label(datentyp_container, text='Datentyp:').grid(row=0, column=0, padx=70, sticky="w")

# Radiobuttons untereinander
tk.Radiobutton(datentyp_container, text='Email', variable=datentyp_var, value='email').grid(row=0, column=1, sticky="w", padx=100)
tk.Radiobutton(datentyp_container, text='MD5', variable=datentyp_var, value='md5').grid(row=1, column=1, sticky="w", padx=100)
tk.Radiobutton(datentyp_container, text='SHA256', variable=datentyp_var, value='sha256').grid(row=2, column=1, sticky="w", padx=100)
tk.Radiobutton(datentyp_container, text='Nur nach Größe teilen', variable=datentyp_var, value='split_only').grid(row=3, column=1, sticky="w", padx=100)

# Dynamische Anpassung der Spaltenbreiten
datentyp_container.grid_columnconfigure(0, weight=1, uniform="equal")  # Label Spalte
datentyp_container.grid_columnconfigure(1, weight=2, uniform="equal")  # Radiobutton Spalte



# Teilgröße für "Nur nach Größe teilen"
teilgroesse_frame = tk.Frame(root)
teilgroesse_frame.grid(row=6, column=0, columnspan=3)

teilgroesse_label = tk.Label(teilgroesse_frame, text='Teilgröße (MB):')
teilgroesse_label.pack(side=tk.LEFT, padx=5)

teilgroesse_entry = tk.Entry(teilgroesse_frame, width=10)
teilgroesse_entry.pack(side=tk.LEFT, padx=5)
teilgroesse_entry.insert(0, "95")

# Status-Anzeige
status_label = tk.Label(root, text='', fg='green', anchor='center', justify='center')
status_label.grid(row=7, column=0, columnspan=3, sticky='ew', pady=5)

# Verarbeiten-Button
verarbeite_button = tk.Button(root, text='Datei verarbeiten', command=verarbeite_datei)
verarbeite_button.grid(row=8, column=0, columnspan=3, pady=10, padx=5)

root.mainloop()
