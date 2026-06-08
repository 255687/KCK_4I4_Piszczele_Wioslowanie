import customtkinter as ctk
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from database import Database

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class MenuApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Asystent Treningu - Menu Główne")
        self.geometry("400x500")
        self.db = Database()
        self.setup_ui()

    def setup_ui(self):
        self.lbl_main_title = ctk.CTkLabel(self, text="Asystent Wiosłowania", font=ctk.CTkFont(size=24, weight="bold"))
        self.lbl_main_title.pack(pady=40)

        self.btn_przejdz_do_treningu = ctk.CTkButton(self, text="Przejdź do Treningu", width=250, height=45,font=ctk.CTkFont(size=15), command=self.otworz_trening)
        self.btn_przejdz_do_treningu.pack(pady=15)

        self.btn_wyswietl_wykres = ctk.CTkButton(self, text="Wyświetl Ostatni Wykres", width=250, height=45,font=ctk.CTkFont(size=15), command=self.otworz_ostatni_wykres)
        self.btn_wyswietl_wykres.pack(pady=15)

        self.btn_wejdz_w_baze = ctk.CTkButton(self, text="Wejdź w Bazę Danych", width=250, height=45,font=ctk.CTkFont(size=15), command=self.otworz_baze)
        self.btn_wejdz_w_baze.pack(pady=15)

    def otworz_trening(self):
        self.withdraw()
        from main import TreningApp
        trening = TreningApp()

        def on_close():
            trening.stop_trening()
            trening.destroy()
            self.deiconify()

        trening.protocol("WM_DELETE_WINDOW", on_close)

    def otworz_ostatni_wykres(self):
        conn = sqlite3.connect(self.db.db_name)
        c = conn.cursor()
        c.execute("SELECT id FROM treningi ORDER BY id DESC LIMIT 1")
        row = c.fetchone()
        if not row:
            conn.close()
            return
        trening_id = row[0]
        c.execute("SELECT numer_serii, poprawne, bledne FROM serie WHERE trening_id = ? ORDER BY numer_serii ASC",(trening_id,))
        dane = c.fetchall()
        conn.close()

        if not dane:
            return

        serie_labels = [f"Seria {row[0]}" for row in dane]
        poprawne = [row[1] for row in dane]
        bledy = [row[2] for row in dane]

        okno = ctk.CTkToplevel(self)
        okno.title(f"Statystyki Ostatniego Treningu (ID: {trening_id})")
        okno.geometry("600x400")

        fig, ax = plt.subplots(figsize=(5, 4))
        x = range(len(serie_labels))
        ax.bar([i - 0.2 for i in x], poprawne, width=0.4, label='Poprawne', color='green')
        ax.bar([i + 0.2 for i in x], bledy, width=0.4, label='Błędy', color='red')
        ax.set_xticks(x)
        ax.set_xticklabels(serie_labels)
        ax.legend()

        canvas = FigureCanvasTkAgg(fig, master=okno)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def otworz_baze(self):
        okno = ctk.CTkToplevel(self)
        okno.title("Historia Treningów")
        okno.geometry("500x400")

        txt = ctk.CTkTextbox(okno, width=460, height=360)
        txt.pack(padx=20, pady=20, fill="both", expand=True)

        conn = sqlite3.connect(self.db.db_name)
        c = conn.cursor()
        c.execute("""
            SELECT t.id, t.data, COUNT(s.id), SUM(s.poprawne), SUM(s.bledne) 
            FROM treningi t 
            LEFT JOIN serie s ON t.id = s.trening_id 
            GROUP BY t.id 
            ORDER BY t.id DESC
        """)
        treningi = c.fetchall()
        conn.close()

        if not treningi:
            txt.insert("0.0", "Brak zapisanych treningów w bazie.")
            txt.configure(state="disabled")
            return

        tekst_bazy = "HISTORIA TRENINGÓW:\n"
        tekst_bazy += "========================================\n"
        for t in treningi:
            t_id, data, ilosc_serii, popr, bled = t
            popr = popr if popr else 0
            bled = bled if bled else 0
            tekst_bazy += f"Trening ID: {t_id} | Data: {data}\n"
            tekst_bazy += f"  Ilość serii: {ilosc_serii}\n"
            tekst_bazy += f"  Suma powtórzeń poprawnych: {popr}\n"
            tekst_bazy += f"  Suma błędów: {bled}\n"
            tekst_bazy += "----------------------------------------\n"

        txt.insert("0.0", tekst_bazy)
        txt.configure(state="disabled")


if __name__ == "__main__":
    app = MenuApp()
    app.mainloop()