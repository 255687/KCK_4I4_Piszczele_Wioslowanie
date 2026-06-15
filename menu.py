import customtkinter as ctk
import sqlite3
import cv2
from PIL import Image
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from database import Database

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class MenuApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Asystent Treningu - Menu Główne")
        self.geometry("450x550")
        self.db = Database()
        self.setup_ui()

    def setup_ui(self):
        self.lbl_main_title = ctk.CTkLabel(self, text="Asystent Wiosłowania", font=ctk.CTkFont(size=24, weight="bold"))
        self.lbl_main_title.pack(pady=40)

        self.btn_przejdz_do_treningu = ctk.CTkButton(self, text="Przejdź do Treningu", width=250, height=45,font=ctk.CTkFont(size=15), command=self.otworz_trening)
        self.btn_przejdz_do_treningu.pack(pady=10)

        self.btn_instrukcja = ctk.CTkButton(self, text="Jak ćwiczyć poprawnie?", width=250, height=45,font=ctk.CTkFont(size=15), command=self.otworz_instrukcje,fg_color="#2b7a4b", hover_color="#1e5c36")
        self.btn_instrukcja.pack(pady=10)

        self.btn_wyswietl_wykres = ctk.CTkButton(self, text="Wyświetl Ostatni Wykres", width=250, height=45,font=ctk.CTkFont(size=15), command=self.otworz_ostatni_wykres)
        self.btn_wyswietl_wykres.pack(pady=10)

        self.btn_wejdz_w_baze = ctk.CTkButton(self, text="Wejdź w Bazę Danych", width=250, height=45,font=ctk.CTkFont(size=15), command=self.otworz_baze)
        self.btn_wejdz_w_baze.pack(pady=10)

    def otworz_trening(self):
        self.withdraw()
        from trening import TreningApp
        trening = TreningApp(self)

        def on_close():
            trening.stop_trening()
            trening.destroy()
            self.deiconify()

        trening.protocol("WM_DELETE_WINDOW", on_close)

    def otworz_instrukcje(self):
        okno = ctk.CTkToplevel(self)
        okno.title("Instrukcja Poprawnego Wykonywania Ćwiczenia")
        okno.geometry("900x500")

        # Lewy panel: Wideo
        video_frame = ctk.CTkFrame(okno)
        video_frame.pack(side="left", padx=20, pady=20, fill="both", expand=True)

        lbl_video_title = ctk.CTkLabel(video_frame, text="Podgląd Poprawnej Techniki", font=ctk.CTkFont(weight="bold"))
        lbl_video_title.pack(pady=5)

        video_label = ctk.CTkLabel(video_frame, text="Ładowanie wideo...")
        video_label.pack(expand=True)

        text_frame = ctk.CTkFrame(okno, width=350)
        text_frame.pack(side="right", padx=20, pady=20, fill="y")

        lbl_title = ctk.CTkLabel(text_frame, text="Krok po Kroku", font=ctk.CTkFont(size=20, weight="bold"))
        lbl_title.pack(pady=10)

        instrukcja_tekst = (
            "1. POZYCJA WYJŚCIOWA:\n"
            "Stań w lekkim rozkroku, stopy na szerokość barków. Złap sztangę nachwytem, nieco szerzej niż szerokość barków.\n\n"
            "2. OPAD TUŁOWIA:\n"
            "Ugnij lekko kolana i pochyl tułów do przodu (utrzymuj plecy proste, kąt nachylenia to około 70-90 stopni).\n\n"
            "3. FAZA KONCENTRYCZNA (Ciągnięcie):\n"
            "Przyciągnij sztangę do dolnej części klatki piersiowej lub górnej części brzucha. Prowadź łokcie blisko tułowia.\n\n"
            "4. ŚCIĄGNIĘCIE ŁOPATEK:\n"
            "W szczytowym momencie ruchu mocno zepnij mięśnie grzbietu i ściągnij łopatki do siebie.\n\n"
            "5. FAZA EKSCENTRYCZNA (Opuszczanie):\n"
            "Opuść sztangę w kontrolowany sposób, powracając do pełnego wyprostu ramion."
        )

        txt_info = ctk.CTkTextbox(text_frame, wrap="word", width=320, height=350, font=ctk.CTkFont(size=13))
        txt_info.pack(pady=10, padx=10)
        txt_info.insert("0.0", instrukcja_tekst)
        txt_info.configure(state="disabled")

        nazwa_pliku_wideo = "wioslowanie_sztanaga_trzymana_nachwytem_do_klatki_w_opadzie_tulowia.mp4"
        cap = cv2.VideoCapture(nazwa_pliku_wideo)

        def graj_wideo():
            if not okno.winfo_exists():
                cap.release()
                return

            if cap.isOpened():
                ret, frame = cap.read()

                if not ret:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = cap.read()

                if ret:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(cv2.resize(frame_rgb, (480, 360)))
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(480, 360))
                    video_label.configure(image=ctk_img, text="")
                    video_label.image = ctk_img
                else:
                    video_label.configure(text="Nie znaleziono pliku wideo w folderze.")

            okno.after(33, graj_wideo)

        graj_wideo()

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