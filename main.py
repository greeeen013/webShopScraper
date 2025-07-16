import tkinter as tk
from tkinter import ttk, messagebox
import requests
from PIL import Image, ImageTk
import io
import sqlite3
from apiScrape import api_get_product_images

DB_PATH = "testdb.sql"

DODAVATELE = {
    "api (161784)": "161784",
    "everit (268493)": "268493",
    "fourcom (312585)": "312585",
    "OCTO IT (348651)": "348651",
    "NetFactory (351191)": "351191"
}


class ObrFormApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Doplnění obrázků k produktům")
        self.root.geometry("1400x900")

        self.conn = None
        self.cursor = None
        self.filtrovane_produkty = []
        self.akt_index = 0
        self.chk_vars = []
        self.img_refs = []
        self.urls = []
        self.vybrany_dodavatel = None

        # Konfigurace databáze
        self.table_name = None
        self.column_mapping = {
            'code': None,  # odpovídá SivCode
            'name': None,  # odpovídá SivName
            'supplier': None,  # odpovídá SivComId
            'notes': None  # odpovídá SivNotePic
        }

        print("[DEBUG] Inicializace GUI...")

        # Nejprve zkontrolujeme databázi
        if not self.check_database_structure():
            return

        self.setup_gui()

    def check_database_structure(self):
        """Zkontroluje strukturu databáze a nastaví mapování sloupců."""
        try:
            self.conn = sqlite3.connect(DB_PATH)
            self.cursor = self.conn.cursor()

            # Získání seznamu tabulek
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in self.cursor.fetchall()]

            if not tables:
                messagebox.showerror("Chyba", "Databáze neobsahuje žádné tabulky!")
                return False

            # Pro jednoduchost vezmeme první tabulku (nebo můžete upravit pro výběr)
            self.table_name = tables[0]
            print(f"[DEBUG] Používám tabulku: {self.table_name}")

            # Získání sloupců v tabulce
            self.cursor.execute(f"PRAGMA table_info({self.table_name})")
            columns = [row[1] for row in self.cursor.fetchall()]
            print(f"[DEBUG] Dostupné sloupce: {columns}")

            # Pokusíme se najít odpovídající sloupce
            for col in columns:
                col_lower = col.lower()
                if 'code' in col_lower:
                    self.column_mapping['code'] = col
                elif 'name' in col_lower:
                    self.column_mapping['name'] = col
                elif 'comid' in col_lower or 'supplier' in col_lower or 'dodavatel' in col_lower:
                    self.column_mapping['supplier'] = col
                elif 'note' in col_lower or 'poznamka' in col_lower or 'pic' in col_lower:
                    self.column_mapping['notes'] = col

            # Ověření, že máme minimálně code a supplier sloupce
            if not self.column_mapping['code'] or not self.column_mapping['supplier']:
                messagebox.showerror("Chyba",
                                     "Nepodařilo se najít potřebné sloupce v tabulce!\n"
                                     f"Potřebujeme sloupce odpovídající: SivCode a SivComId\n"
                                     f"Nalezené sloupce: {columns}")
                return False

            print(f"[DEBUG] Mapování sloupců: {self.column_mapping}")
            return True

        except Exception as e:
            messagebox.showerror("Chyba", f"Chyba při připojování k databázi:\n{e}")
            return False

    def setup_gui(self):
        """Vytvoří GUI prvky aplikace."""
        self.combo = ttk.Combobox(self.root, values=list(DODAVATELE.keys()), state="readonly", font=("Arial", 16))
        self.combo.bind("<<ComboboxSelected>>", self.combo_selected)
        self.combo.pack(pady=10)

        self.label_info = tk.Label(self.root, text="", font=("Arial", 18, "bold"))
        self.label_info.pack(pady=10)

        self.canvas = tk.Canvas(self.root)
        self.scroll_y = tk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scroll_y.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scroll_y.pack(side="right", fill="y")

        self.frame_obrazky = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.frame_obrazky, anchor="nw")
        self.frame_obrazky.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self.btn_frame = tk.Frame(self.root)
        self.btn_frame.pack(pady=20)
        tk.Button(self.btn_frame, text="Potvrdit", command=self.potvrdit, font=("Arial", 16), height=2, width=12).pack(
            side="left", padx=20)
        tk.Button(self.btn_frame, text="Zrušit", command=self.zrusit, font=("Arial", 16), height=2, width=12).pack(
            side="left", padx=20)
        tk.Button(self.btn_frame, text="💾 Uložit DB", command=self.zapis_db, font=("Arial", 12)).pack(side="left",
                                                                                                      padx=20)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def combo_selected(self, event):
        self.vybrany_dodavatel = self.combo.get()
        kod = DODAVATELE[self.vybrany_dodavatel]
        print(f"[DEBUG] Vybrán dodavatel: {self.vybrany_dodavatel} (SivComId: {kod})")

        self.filtrovane_produkty = []
        try:
            query = f"""
                SELECT * FROM {self.table_name} 
                WHERE {self.column_mapping['supplier']} = ? 
                AND ({self.column_mapping['notes']} IS NULL OR {self.column_mapping['notes']} = '')
            """
            self.cursor.execute(query, (kod,))
            rows = self.cursor.fetchall()

            # Convert to list of dictionaries
            columns = [column[0] for column in self.cursor.description]
            self.filtrovane_produkty = [dict(zip(columns, row)) for row in rows]

            print(f"[DEBUG] Celkem vyhovujících produktů: {len(self.filtrovane_produkty)}")
        except Exception as e:
            print(f"[CHYBA] Při načítání z databáze: {e}")
            messagebox.showerror("Chyba", f"Chyba při načítání z databáze:\n{e}")
            return

        self.akt_index = 0
        if not self.filtrovane_produkty:
            messagebox.showinfo("Info", "Žádné produkty k doplnění.")
            return
        self.nacti_obrazky()

    def zapis_db(self):
        print("[DEBUG] Ukládání změn do databáze...")
        try:
            self.conn.commit()
            print("[DEBUG] Změny úspěšně uloženy do databáze.")
            messagebox.showinfo("Info", "Změny úspěšně uloženy do databáze.")
        except Exception as e:
            print(f"[CHYBA] Při ukládání do databáze: {e}")
            messagebox.showerror("Chyba", f"Chyba při ukládání do databáze:\n{e}")

    def nacti_obrazky(self):
        for widget in self.frame_obrazky.winfo_children():
            widget.destroy()
        self.chk_vars.clear()
        self.img_refs.clear()
        self.urls.clear()

        if self.akt_index >= len(self.filtrovane_produkty):
            self.zapis_db()
            messagebox.showinfo("Hotovo", "Žádné další produkty.")
            return

        produkt = self.filtrovane_produkty[self.akt_index]
        kod = produkt[self.column_mapping['code']]
        nazev = produkt.get(self.column_mapping['name'], "")

        self.label_info.config(text=f"{kod} - {nazev}")

        try:
            if self.vybrany_dodavatel.startswith("api"):
                self.urls = api_get_product_images(kod)
                print(f"[DEBUG] Načteno {len(self.urls)} obrázků pro {kod}.")
            else:
                messagebox.showwarning("Chyba", "Dodavatel zatím není podporován.")
                return
        except Exception as e:
            print(f"[CHYBA] Při načítání obrázků: {e}")
            self.zrusit()
            return

        for i, url in enumerate(self.urls):
            try:
                r = requests.get(url, timeout=5)
                img = Image.open(io.BytesIO(r.content))
                img.thumbnail((400, 400))
                photo = ImageTk.PhotoImage(img)
                self.img_refs.append(photo)

                frame = tk.Frame(self.frame_obrazky)
                frame.grid(row=i // 2, column=i % 2, padx=20, pady=10, sticky="nw")

                var = tk.IntVar(value=1)
                chk = tk.Checkbutton(frame, variable=var, font=("Arial", 14))
                chk.pack()
                chk.bind("<Button-1>", lambda e, v=var: v.set(0 if v.get() else 1))

                label = tk.Label(frame, image=photo)
                label.pack()
                label.bind("<Button-1>", lambda e, v=var: v.set(0 if v.get() else 1))

                self.chk_vars.append(var)

                print(f"[DEBUG] Obrázek {i + 1}: {url}")
            except Exception as e:
                print(f"[CHYBA] Obrázek {url} nelze načíst: {e}")

    def potvrdit(self):
        vybrane_urls = [url for url, var in zip(self.urls, self.chk_vars) if var.get() == 1]
        produkt = self.filtrovane_produkty[self.akt_index]
        kod = produkt[self.column_mapping['code']]

        if vybrane_urls:
            zapis = ";\n".join(vybrane_urls) + ";"
            print("[DEBUG] Hodnota pro zápis do poznámek:")
            print(zapis)

            try:
                query = f"""
                    UPDATE {self.table_name} 
                    SET {self.column_mapping['notes']} = ? 
                    WHERE {self.column_mapping['code']} = ?
                """
                self.cursor.execute(query, (zapis, kod))
                produkt[self.column_mapping['notes']] = zapis
                print("[DEBUG] Databáze aktualizována!")
            except Exception as e:
                print(f"[CHYBA] Při aktualizaci databáze: {e}")
                messagebox.showerror("Chyba", f"Chyba při aktualizaci databáze:\n{e}")
                return
        else:
            print(f"[DEBUG] Produkt {kod} potvrzen bez výběru obrázků")

        self.akt_index += 1
        self.nacti_obrazky()

    def zrusit(self):
        produkt = self.filtrovane_produkty[self.akt_index]
        print(f"[DEBUG] Produkt {produkt[self.column_mapping['code']]} přeskočen.")
        self.akt_index += 1
        self.nacti_obrazky()

    def __del__(self):
        if self.conn:
            self.conn.close()
            print("[DEBUG] Databázové připojení uzavřeno.")


if __name__ == "__main__":
    print("[DEBUG] Spouštím aplikaci...")
    root = tk.Tk()
    app = ObrFormApp(root)
    root.mainloop()