import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import os

# Liste für die ausgewählten Dateien
selected_files = []

def add_file():
    file = filedialog.askopenfilename(
        title="Wähle eine Datei aus",
        filetypes=[("CSV und Text Dateien", "*.csv *.txt")]
    )
    if file:
        selected_files.append(file)
        update_file_list()

def update_file_list():
    listbox.delete(0, tk.END)
    for file in selected_files:
        listbox.insert(tk.END, os.path.basename(file))

def clear_file_list():
    selected_files.clear()
    listbox.delete(0, tk.END)

def merge_files():
    if not selected_files:
        messagebox.showwarning("Keine Dateien", "Bitte füge mindestens eine Datei hinzu.")
        return

    email_set = set()

    for file in selected_files:
        read_successful = False

        for sep in [',', ';', '\t']:
            try:
                # Erst mit UTF-8, sonst Latin-1
                try:
                    df = pd.read_csv(file, sep=sep, header=None, encoding="utf-8")
                except UnicodeDecodeError:
                    df = pd.read_csv(file, sep=sep, header=None, encoding="ISO-8859-1")

                if df.shape[1] >= 1:
                    emails = df.iloc[:, 0].dropna().astype(str).tolist()
                    email_set.update(email.strip() for email in emails)
                    read_successful = True
                    break
            except Exception:
                continue

        if not read_successful:
            messagebox.showerror("Lesefehler", f"Datei '{os.path.basename(file)}' konnte nicht gelesen werden.")
            return

    if not email_set:
        messagebox.showinfo("Keine Daten", "Keine E-Mail-Adressen gefunden.")
        return

    unique_emails = sorted(email_set)

    output_file = filedialog.asksaveasfilename(
        title="Speichere zusammengeführte Datei",
        defaultextension=".txt",
        filetypes=[("Textdatei", "*.txt")]
    )

    if output_file:
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                for email in unique_emails:
                    f.write(email + "\n")
            messagebox.showinfo(
                "Fertig",
                f"{len(unique_emails)} eindeutige E-Mail-Adressen gespeichert in:\n{output_file}"
            )
        except Exception as e:
            messagebox.showerror("Speicherfehler", f"Fehler beim Speichern:\n{e}")

# GUI-Setup
root = tk.Tk()
root.title("E-Mail-Dateien zusammenfügen")
root.geometry("450x420")

title_label = tk.Label(root, text="Einzeln .csv oder .txt Dateien hinzufügen", font=("Arial", 12))
title_label.pack(pady=10)

add_button = tk.Button(root, text="Datei hinzufügen", command=add_file, bg="#2196F3", fg="white", font=("Arial", 10))
add_button.pack(pady=5)

clear_button = tk.Button(root, text="Liste leeren", command=clear_file_list, font=("Arial", 10))
clear_button.pack(pady=2)

listbox = tk.Listbox(root, width=50)
listbox.pack(pady=10)

merge_button = tk.Button(root, text="Dateien zusammenführen", command=merge_files, bg="#4CAF50", fg="white", font=("Arial", 12))
merge_button.pack(pady=10)

exit_button = tk.Button(root, text="Beenden", command=root.quit, font=("Arial", 10))
exit_button.pack(pady=5)

root.mainloop()
