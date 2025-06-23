import os
import tkinter as tk
from tkinter import filedialog, messagebox

def split_file_by_line(input_file, chunk_size_mb):
    if not os.path.exists(input_file):
        messagebox.showerror("Fehler", f"Die Eingabedatei '{input_file}' wurde nicht gefunden.")
        return

    output_folder = os.path.splitext(input_file)[0] + "_BL"
    os.makedirs(output_folder, exist_ok=True)

    chunk_size_bytes = int(chunk_size_mb * 1024 * 1024)
    
    with open(input_file, 'r', encoding='utf-8') as infile:
        chunk_number = 1
        chunk_data = []
        current_chunk_size = 0

        for line in infile:
            chunk_data.append(line)
            current_chunk_size += len(line.encode('utf-8'))

            if current_chunk_size >= chunk_size_bytes:
                output_file_path = os.path.join(output_folder, f'chunk_{chunk_number}.csv')
                with open(output_file_path, 'w', encoding='utf-8') as outfile:
                    outfile.writelines(chunk_data)

                print(f'Chunk {chunk_number} geschrieben: {output_file_path}')
                chunk_data = []
                current_chunk_size = 0
                chunk_number += 1

        # Den letzten Chunk speichern, falls noch Daten vorhanden sind
        if chunk_data:
            output_file_path = os.path.join(output_folder, f'chunk_{chunk_number}.csv')
            with open(output_file_path, 'w', encoding='utf-8') as outfile:
                outfile.writelines(chunk_data)

            print(f'Chunk {chunk_number} geschrieben: {output_file_path}')

    messagebox.showinfo("Erfolg", f"Die Datei wurde erfolgreich in {chunk_number} Chunks aufgeteilt.")

def choose_file():
    input_file = filedialog.askopenfilename(title="Wähle eine Datei aus", filetypes=[("CSV oder TXT Dateien", "*.csv *.txt")])
    if input_file:
        entry_file.delete(0, tk.END)
        entry_file.insert(0, input_file)

def start_splitting():
    input_file = entry_file.get()
    try:
        chunk_size_mb = float(entry_size.get())
    except ValueError:
        messagebox.showerror("Fehler", "Bitte gib eine gültige Zahl für die Chunk-Größe an.")
        return

    if not input_file:
        messagebox.showerror("Fehler", "Bitte wähle eine Datei aus.")
        return
    
    split_file_by_line(input_file, chunk_size_mb)

# GUI erstellen
root = tk.Tk()
root.title("Datei-Splitter")

# Dateiauswahl
label_file = tk.Label(root, text="Eingabedatei:")
label_file.grid(row=0, column=0, padx=10, pady=10)
entry_file = tk.Entry(root, width=40)
entry_file.grid(row=0, column=1, padx=10, pady=10)
button_browse = tk.Button(root, text="Durchsuchen", command=choose_file)
button_browse.grid(row=0, column=2, padx=10, pady=10)

# Chunk-Größe
label_size = tk.Label(root, text="Chunk-Größe (MB):")
label_size.grid(row=1, column=0, padx=10, pady=10)
entry_size = tk.Entry(root, width=10)
entry_size.grid(row=1, column=1, padx=10, pady=10)

# Start-Button
button_start = tk.Button(root, text="Datei aufteilen", command=start_splitting)
button_start.grid(row=2, column=1, padx=10, pady=10)

root.mainloop()
