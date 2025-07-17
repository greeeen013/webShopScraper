import tkinter as tk
from tkinter import ttk, messagebox
import requests
from PIL import Image, ImageTk
import io
import pyodbc
import threading
import queue
import asyncio

DODAVATELE = {
    "api (161784)": "161784",
    "everit (268493)": "268493",
    "fourcom (312585)": "312585",
    "OCTO IT (348651)": "348651",
    "NetFactory (351191)": "351191"
}

POCTY_PRODUKTU = [25, 50, 75, 100]
OBRAZKY_NA_RADEK = ["2", "3", "4", "5", "6", "nekonečno"]


class ObrFormApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Doplnění obrázků k produktům")
        self.root.geometry("1400x900")

        self.conn = None
        self.cursor = None
        self.filtrovane_produkty = []
        self.img_refs = {}
        self.vybrany_dodavatel = None
        self.df = None
        self.produkty_k_zpracovani = []
        self.produkt_widgety = {}
        self.buffer_size = 25
        self.image_queue = queue.Queue()
        self.loading_threads = []
        self.all_check_var = tk.BooleanVar(value=False)
        self.produkt_check_vars = {}
        self.image_check_vars = {}
        self.loading_active = False
        self.max_threads = 10
        self.obrazky_na_radek = 4  # Výchozí hodnota
        self.scrollregion_scheduled = False

        # Konfigurace databáze
        self.table_name = "StoItemCom"
        self.column_mapping = {
            'code': 'SivCode',
            'name': 'SivName',
            'supplier': 'SivComId',
            'notes': 'SivNotePic'
        }

        print("[DEBUG] Inicializace GUI...")
        self.setup_gui()

    def connect_to_database(self):
        """Připojí se k SQL Serveru"""
        try:
            server = '192.168.1.14'
            database = 'i6ABCtest'
            username = 'test'
            password = 'test'

            conn_str = (
                f'DRIVER={{SQL Server}};'
                f'SERVER={server};'
                f'DATABASE={database};'
                f'UID={username};'
                f'PWD={password}'
            )

            print("[DEBUG] Pokus o připojení k databázi...")
            self.conn = pyodbc.connect(conn_str)
            self.cursor = self.conn.cursor()
            print("[DEBUG] Úspěšně připojeno k SQL Serveru")
            return True
        except Exception as e:
            print(f"[CHYBA] Připojení k databázi: {str(e)}")
            messagebox.showerror("Chyba", f"Chyba při připojování k databázi:\n{str(e)}")
            return False

    def check_database_structure(self):
        """Zkontroluje existenci potřebných sloupců"""
        try:
            required_columns = ['SivCode', 'SivComId', 'SivNotePic', 'SivName']

            query = f"""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = '{self.table_name}'
            """
            self.cursor.execute(query)
            existing_columns = [row.COLUMN_NAME for row in self.cursor.fetchall()]

            missing_columns = [col for col in required_columns if col not in existing_columns]

            if missing_columns:
                messagebox.showerror("Chyba",
                                     f"V tabulce chybí potřebné sloupce!\n"
                                     f"Chybějící sloupce: {', '.join(missing_columns)}")
                return False

            print("[DEBUG] Všechny potřebné sloupce existují")
            return True

        except Exception as e:
            print(f"[CHYBA] Při kontrole struktury databáze: {str(e)}")
            messagebox.showerror("Chyba", f"Chyba při kontrole struktury databáze:\n{str(e)}")
            return False

    def setup_gui(self):
        """Vytvoří GUI prvky aplikace."""
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=10)

        # Combobox pro výběr dodavatele
        tk.Label(top_frame, text="Dodavatel:", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
        self.combo_dodavatel = ttk.Combobox(top_frame, values=list(DODAVATELE.keys()), state="readonly",
                                            font=("Arial", 12), width=20)
        self.combo_dodavatel.pack(side=tk.LEFT, padx=5)
        self.combo_dodavatel.bind("<<ComboboxSelected>>", self.combo_selected)

        # Combobox pro výběr počtu produktů
        tk.Label(top_frame, text="Počet produktů:", font=("Arial", 12)).pack(side=tk.LEFT, padx=(20, 5))
        self.combo_pocet = ttk.Combobox(top_frame, values=POCTY_PRODUKTU, state="readonly", font=("Arial", 12),
                                        width=10)
        self.combo_pocet.current(0)
        self.combo_pocet.pack(side=tk.LEFT, padx=5)

        # Combobox pro výběr počtu obrázků na řádek
        tk.Label(top_frame, text="Obrázky na řádek:", font=("Arial", 12)).pack(side=tk.LEFT, padx=(20, 5))
        self.combo_obrazky_na_radek = ttk.Combobox(top_frame, values=OBRAZKY_NA_RADEK, state="readonly",
                                                   font=("Arial", 12), width=10)
        self.combo_obrazky_na_radek.current(2)  # Výchozí hodnota 4
        self.combo_obrazky_na_radek.pack(side=tk.LEFT, padx=5)
        self.combo_obrazky_na_radek.bind("<<ComboboxSelected>>", self.update_obrazky_na_radek)

        # Checkbox "Vybrat vše"
        self.chk_all = tk.Checkbutton(top_frame, text="Vybrat vše", variable=self.all_check_var,
                                      font=("Arial", 12), command=self.toggle_all)
        self.chk_all.pack(side=tk.LEFT, padx=20)

        # Canvas s scrollbarem
        self.canvas_frame = tk.Frame(self.root)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(self.canvas_frame)
        self.scroll_y = tk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scroll_y.set)

        self.scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.inner_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor=tk.NW)

        self.inner_frame.bind("<Configure>", lambda e: self.schedule_scrollregion_update())
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.inner_frame.bind("<MouseWheel>", self._on_mousewheel)

        # Tlačítka dole
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Potvrdit", command=self.potvrdit_vse,
                  font=("Arial", 14), height=2, width=15).pack(side=tk.LEFT, padx=20)
        tk.Button(btn_frame, text="Zrušit", command=self.zrusit_vse,
                  font=("Arial", 14), height=2, width=15).pack(side=tk.LEFT, padx=20)

    def schedule_scrollregion_update(self):
        """Plánuje aktualizaci scrollregionu pro plynulejší scrollování."""
        if not self.scrollregion_scheduled:
            self.scrollregion_scheduled = True
            self.root.after(100, self.update_scrollregion)

    def update_scrollregion(self):
        """Aktualizuje scrollregion canvasu."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.scrollregion_scheduled = False

    def update_obrazky_na_radek(self, event=None):
        """Aktualizuje počet obrázků na řádek podle výběru uživatele."""
        vyber = self.combo_obrazky_na_radek.get()
        if vyber == "nekonečno":
            self.obrazky_na_radek = float('inf')
        else:
            self.obrazky_na_radek = int(vyber)

        # Přerozdělení obrázků podle nového nastavení
        for kod, data in self.produkt_widgety.items():
            self.reorganize_images(data['images_frame'], data['urls'])

    def reorganize_images(self, frame, urls):
        """Přerozdělí obrázky v frame podle aktuálního nastavení počtu na řádek."""
        # Odstranění všech obrázků z frame
        for widget in frame.winfo_children():
            widget.destroy()

        # Vytvoření nových frame pro řádky
        current_row = 0
        current_col = 0
        row_frame = None

        for i, url in enumerate(urls):
            if current_col % self.obrazky_na_radek == 0:
                row_frame = tk.Frame(frame)
                row_frame.pack(fill=tk.X)
                current_col = 0

            kod = DODAVATELE[self.vybrany_dodavatel]
            # Vytvoření frame pro obrázek
            img_frame = tk.Frame(row_frame)
            img_frame.grid(row=0, column=current_col, padx=5, pady=5)
            current_col += 1

            # Checkbox
            img_var = self.image_check_vars[kod][i]
            chk = tk.Checkbutton(
                img_frame,
                variable=img_var,
                command=lambda k=kod: self.update_product_check(k)
            )
            chk.pack()

            # Label s obrázkem
            label = tk.Label(img_frame, image=self.img_refs[kod][i])
            label.image = self.img_refs[kod][i]
            label.pack()
            label.bind("<Button-1>", lambda e, var=img_var: var.set(not var.get()))

    def _on_mousewheel(self, event):
        """Zpracování scrollování myší s akcelerací."""
        scroll_amount = int(-1 * (event.delta / 40))
        self.canvas.yview_scroll(scroll_amount, "units")

    def combo_selected(self, event):
        """Zpracuje výběr dodavatele a počtu produktů."""
        self.vybrany_dodavatel = self.combo_dodavatel.get()
        self.buffer_size = int(self.combo_pocet.get())
        kod = DODAVATELE[self.vybrany_dodavatel]

        print(f"[DEBUG] Vybrán dodavatel: {self.vybrany_dodavatel}, počet: {self.buffer_size}")

        # Připojení k databázi
        if not self.connect_to_database():
            return

        if not self.check_database_structure():
            self.close_database()
            return

        try:
            # Načtení produktů
            query = f"""
                SELECT TOP {self.buffer_size} SivCode, SivName 
                FROM [{self.table_name}] 
                WHERE [{self.column_mapping['supplier']}] = ? 
                AND ([{self.column_mapping['notes']}] IS NULL OR [{self.column_mapping['notes']}] = '')
            """
            print(f"[DEBUG] Provádím dotaz: {query}")
            self.cursor.execute(query, (kod,))
            self.filtrovane_produkty = [
                {'SivCode': row.SivCode, 'SivName': row.SivName}
                for row in self.cursor.fetchall()
            ]

            print(f"[DEBUG] Načteno {len(self.filtrovane_produkty)} produktů")

            # Uzavření databáze
            self.close_database()

            if not self.filtrovane_produkty:
                messagebox.showinfo("Info", "Žádné produkty k doplnění.")
                return

            # Vyčištění GUI
            for widget in self.inner_frame.winfo_children():
                widget.destroy()

            self.produkty_k_zpracovani = self.filtrovane_produkty[:]
            self.produkt_widgety = {}
            self.produkt_check_vars = {}
            self.image_check_vars = {}
            self.img_refs = {}
            self.all_check_var.set(False)

            # Spuštění asynchronního načítání obrázků
            self.start_async_image_loading()

        except Exception as e:
            print(f"[CHYBA] Při načítání produktů: {e}")
            messagebox.showerror("Chyba", f"Chyba při načítání produktů:\n{e}")
            self.close_database()

    def start_async_image_loading(self):
        """Spustí asynchronní načítání obrázků s optimalizovaným počtem vláken."""
        if not self.loading_active:
            self.loading_active = True
            print(f"[THREAD] Spouštím {self.max_threads} vláken")

            for _ in range(min(self.max_threads, len(self.produkty_k_zpracovani))):
                if self.produkty_k_zpracovani:
                    produkt = self.produkty_k_zpracovani.pop(0)
                    t = threading.Thread(target=self.load_product_images, args=(produkt,))
                    t.daemon = True
                    t.start()
                    self.loading_threads.append(t)

            # Pravidelně kontrolovat stav
            self.root.after(500, self.check_threads)

    def check_threads(self):
        """Kontroluje stav načítacích vláken a spouští nová podle potřeby."""
        alive_threads = [t for t in self.loading_threads if t.is_alive()]
        self.loading_threads = alive_threads

        if not alive_threads and not self.produkty_k_zpracovani:
            self.loading_active = False
            print("[THREAD] Všechna vlákna dokončena")
        else:
            # Spustit další vlákna pokud je volná kapacita
            free_slots = self.max_threads - len(alive_threads)
            for _ in range(min(free_slots, len(self.produkty_k_zpracovani))):
                if self.produkty_k_zpracovani:
                    produkt = self.produkty_k_zpracovani.pop(0)
                    t = threading.Thread(target=self.load_product_images, args=(produkt,))
                    t.daemon = True
                    t.start()
                    self.loading_threads.append(t)

            self.root.after(500, self.check_threads)

    def load_product_images(self, produkt):
        """Načte obrázky pro produkt ve vlákně."""
        try:
            kod = produkt['SivCode']
            print(f"[THREAD] Načítám obrázky pro produkt: {kod}")

            # Nejprve získej URL obrázků
            from apiScrape import api_get_product_images
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            urls = loop.run_until_complete(api_get_product_images(kod))
            loop.close()

            # Pokud nejsou žádné obrázky, přeskoč tento produkt
            if not urls:
                print(f"[INFO] Žádné obrázky pro produkt {kod}, přeskočeno")
                return

            # Zobraz produkt pouze pokud má obrázky
            self.root.after(0, lambda: self.display_product_with_images(produkt))

            # Načti a zobraz obrázky
            for url in urls:
                try:
                    r = requests.get(url, timeout=10)
                    img = Image.open(io.BytesIO(r.content))
                    img.thumbnail((300, 300))
                    photo = ImageTk.PhotoImage(img)

                    # Přidej obrázek do GUI
                    self.root.after_idle(self.add_single_image, produkt, url, photo)
                except Exception as e:
                    print(f"[CHYBA] Obrázek {url} nelze načíst: {e}")

        except Exception as e:
            print(f"[CHYBA] Při načítání obrázků: {e}")

    def display_product_with_images(self, produkt):
        """Zobrazí základní informace o produktu."""
        kod = produkt['SivCode']
        nazev = produkt.get('SivName', "")

        # Pokud už byl produkt zobrazen, přeskočíme
        if kod in self.produkt_widgety:
            return

        # Frame pro celý produkt
        frame_produkt = tk.LabelFrame(
            self.inner_frame,
            text=f"{kod} - {nazev}",
            font=("Arial", 12, "bold"),
            padx=10,
            pady=10,
            width=800  # Pevná šířka pro stabilitu
        )
        frame_produkt.pack(fill=tk.X, padx=10, pady=5, ipadx=5, ipady=5)
        frame_produkt.grid_columnconfigure(0, weight=1)

        # Checkbox pro výběr všech obrázků v produktu
        var_produkt = tk.BooleanVar(value=False)
        self.produkt_check_vars[kod] = var_produkt
        chk_produkt = tk.Checkbutton(
            frame_produkt,
            text="Vybrat všechny obrázky",
            variable=var_produkt,
            font=("Arial", 10),
            command=lambda k=kod: self.toggle_product_images(k)
        )
        chk_produkt.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))

        # Frame pro obrázky
        frame_obrazky = tk.Frame(frame_produkt)
        frame_obrazky.grid(row=1, column=0, sticky=tk.W)

        # Uložení widgetů
        self.produkt_widgety[kod] = {
            'frame': frame_produkt,
            'images_frame': frame_obrazky,
            'image_vars': [],
            'urls': [],
            'produkt': produkt
        }
        self.image_check_vars[kod] = []

        # Aktualizovat GUI
        self.canvas.update_idletasks()

    def add_single_image(self, produkt, url, photo):
        """Přidá jeden načtený obrázek k produktu."""
        kod = produkt['SivCode']

        # Pokud byl produkt mezitím odstraněn, přeskoč
        if kod not in self.produkt_widgety:
            return

        # Uložení reference
        if kod not in self.img_refs:
            self.img_refs[kod] = []
        self.img_refs[kod].append(photo)

        # Vytvoření frame pro obrázek
        img_frame = tk.Frame(self.produkt_widgety[kod]['images_frame'])

        # Rozložení podle počtu obrázků na řádek
        if self.obrazky_na_radek == float('inf'):
            img_frame.pack(side=tk.LEFT, padx=5, pady=5)
        else:
            # Pokud máme omezený počet na řádek, použijeme grid
            row = len(self.produkt_widgety[kod]['urls']) // self.obrazky_na_radek
            col = len(self.produkt_widgety[kod]['urls']) % self.obrazky_na_radek
            img_frame.grid(row=row, column=col, padx=5, pady=5)

        # Checkbox
        img_var = tk.BooleanVar(value=False)
        self.image_check_vars[kod].append(img_var)
        self.produkt_widgety[kod]['image_vars'].append(img_var)

        chk = tk.Checkbutton(
            img_frame,
            variable=img_var,
            command=lambda k=kod: self.update_product_check(k)
        )
        chk.pack()

        # Label s obrázkem a bind na kliknutí
        label = tk.Label(img_frame, image=photo)
        label.image = photo
        label.pack()
        label.bind("<Button-1>", lambda e, var=img_var: var.set(not var.get()))

        # Uložit URL
        self.produkt_widgety[kod]['urls'].append(url)

    def toggle_all(self):
        """Vybere nebo zruší výběr všech obrázků u všech produktů."""
        select = self.all_check_var.get()
        for kod in self.produkt_check_vars:
            self.produkt_check_vars[kod].set(select)
            self.toggle_product_images(kod, select)

    def toggle_product_images(self, kod, value=None):
        """Vybere nebo zruší výběr všech obrázků v produktu."""
        if value is None:
            value = self.produkt_check_vars[kod].get()

        for var in self.image_check_vars[kod]:
            var.set(value)

    def update_product_check(self, kod):
        """Aktualizuje stav checkboxu produktu na základě obrázků."""
        all_checked = all(var.get() for var in self.image_check_vars[kod])
        any_checked = any(var.get() for var in self.image_check_vars[kod])

        if all_checked:
            self.produkt_check_vars[kod].set(True)
        elif any_checked:
            # Pro částečný výběr necháme checkbox v "částečném" stavu
            pass
        else:
            self.produkt_check_vars[kod].set(False)

    def potvrdit_vse(self):
        """Potvrdí všechny vybrané produkty a uloží je do databáze."""
        if not self.connect_to_database():
            return

        try:
            for kod, data in self.produkt_widgety.items():
                vybrane_urls = [
                    url for i, url in enumerate(data['urls'])
                    if i < len(data['image_vars']) and data['image_vars'][i].get()
                ]

                if vybrane_urls:
                    produkt = data['produkt']
                    zapis = ";\n".join(vybrane_urls) + ";"

                    query = f"""
                        UPDATE [{self.table_name}] 
                        SET [{self.column_mapping['notes']}] = ? 
                        WHERE [{self.column_mapping['code']}] = ?
                    """
                    self.cursor.execute(query, (zapis, produkt['SivCode']))

            self.conn.commit()
            messagebox.showinfo("Info", "Všechny vybrané produkty byly uloženy.")

            # Odstranění uložených produktů z GUI
            for kod in list(self.produkt_widgety.keys()):
                self.produkt_widgety[kod]['frame'].destroy()
                del self.produkt_widgety[kod]
                if kod in self.img_refs:
                    del self.img_refs[kod]

        except Exception as e:
            print(f"[CHYBA] Při ukládání do DB: {e}")
            messagebox.showerror("Chyba", f"Chyba při ukládání:\n{e}")
        finally:
            self.close_database()

    def zrusit_vse(self):
        """Zruší všechny produkty bez uložení."""
        for kod in list(self.produkt_widgety.keys()):
            self.produkt_widgety[kod]['frame'].destroy()
            del self.produkt_widgety[kod]
            if kod in self.img_refs:
                del self.img_refs[kod]
        messagebox.showinfo("Info", "Všechny produkty byly zrušeny.")

    def close_database(self):
        """Uzavře databázové připojení."""
        if self.conn:
            try:
                self.conn.close()
                print("[DEBUG] Databázové připojení uzavřeno.")
            except:
                pass
            finally:
                self.conn = None
                self.cursor = None


if __name__ == "__main__":
    print("[DEBUG] Spouštím aplikaci...")
    root = tk.Tk()
    app = ObrFormApp(root)
    root.mainloop()