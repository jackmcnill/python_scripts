import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import os

def clean_email_file(lines):
    # E-Mails bereinigen und leere Zeilen entfernen
    cleaned_lines = [line.strip().replace('"', '') + '\n' for line in lines if line.strip()]
    return cleaned_lines

def update_preview(text_widget, lines):
    # Textfeld aktualisieren
    text_widget.config(state=tk.NORMAL)
    text_widget.delete(1.0, tk.END)
    text_widget.insert(tk.END, "".join(lines))
    text_widget.config(state=tk.DISABLED)

def process_file(file_path, lines, preview_widget):
    try:
        # Bereinigte Datei speichern
        cleaned_lines = clean_email_file(lines)
        cleaned_file_path = file_path.replace('.csv', '_cleaned.csv').replace('.txt', '_cleaned.txt')
        with open(cleaned_file_path, 'w', encoding='utf-8') as file:
            file.writelines(cleaned_lines)

        messagebox.showinfo("Erfolg", f"Die Datei wurde erfolgreich bereinigt. Gespeichert unter:\n{cleaned_file_path}")

        # Vorschau der bereinigten Datei anzeigen
        update_preview(preview_widget, cleaned_lines)

    except Exception as e:
        messagebox.showerror("Fehler", f"Beim Verarbeiten der Datei ist ein Fehler aufgetreten: {e}")

def select_file(preview_widget, process_button):
    file_path = filedialog.askopenfilename(
        title="Wähle eine Datei aus",
        filetypes=(
            ("Textdateien", "*.txt"),
            ("CSV-Dateien", "*.csv"),
        ),
    )

    if not file_path:
        return

    if not os.path.isfile(file_path):
        messagebox.showerror("Fehler", "Die ausgewählte Datei existiert nicht.")
        return

    try:
        # Datei lesen
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        # Originaldatei-Vorschau anzeigen
        update_preview(preview_widget, lines)

        # Aktivieren des Bereinigungs-Buttons
        process_button.config(
            state=tk.NORMAL,
            command=lambda: process_file(file_path, lines, preview_widget)
        )

    except Exception as e:
        messagebox.showerror("Fehler", f"Die Datei konnte nicht gelesen werden: {e}")

def main():
    # Hauptfenster erstellen
    root = tk.Tk()
    root.title("E-Mail-Reiniger")

    # Fenstergröße und Layout
    root.geometry("600x500")
    root.resizable(False, False)

    # Beschreibung
    description_label = tk.Label(
        root,
        text="Wähle eine .csv- oder .txt-Datei aus, um E-Mails von Anführungszeichen zu bereinigen und leere Zeilen zu entfernen. Vorschau wird unten angezeigt.",
        wraplength=580,
        justify="center",
    )
    description_label.pack(pady=10)

    # Vorschau-Textfeld
    preview_widget = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=70, height=20, state=tk.DISABLED)
    preview_widget.pack(pady=10)

    # Button zum Auswählen der Datei
    process_button = tk.Button(
        root,
        text="Bereinigung starten",
        state=tk.DISABLED,
        width=20,
        height=2,
    )

    select_file_button = tk.Button(
        root,
        text="Datei auswählen",
        command=lambda: select_file(preview_widget, process_button),
        width=20,
        height=2,
    )
    select_file_button.pack(pady=10)

    # Button für Bereinigung
    process_button.pack(pady=10)

    # Haupt-Loop starten
    root.mainloop()

if __name__ == "__main__":
    main()
