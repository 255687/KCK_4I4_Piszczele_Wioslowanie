import cv2
import mediapipe as mp
import customtkinter as ctk
import sqlite3
import pyttsx3
import threading
import queue
import math
from datetime import datetime
from PIL import Image
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

#BAZA DANYCH

def init_db():
    conn = sqlite3.connect('trening_db.sqlite')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS statystyki (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT,
                    poprawne INTEGER,
                    bledne INTEGER
                )''')
    conn.commit()
    conn.close()

def zapisz_trening(poprawne, bledne):
    conn = sqlite3.connect('trening_db.sqlite')
    c = conn.cursor()
    c.execute("INSERT INTO statystyki (data, poprawne, bledne) VALUES (?, ?, ?)",
              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), poprawne, bledne))
    conn.commit()
    conn.close()

#SILNIK GŁOSOWY

audio_queue = queue.Queue()

def tts_worker():
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    while True:
        text = audio_queue.get()
        if text is None: break
        engine.say(text)
        engine.runAndWait()
        audio_queue.task_done()

tts_thread = threading.Thread(target=tts_worker, daemon=True)
tts_thread.start()

def powiedz(tekst):
    audio_queue.put(tekst)

#MATEMATYKA

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

def oblicz_kat(p1, p2, p3):
    kat = math.degrees(math.atan2(p3[1] - p2[1], p3[0] - p2[0]) - math.atan2(p1[1] - p2[1], p1[0] - p2[0]))
    kat = abs(kat)
    if kat > 180.0:
        kat = 360.0 - kat
    return kat

#GŁÓWNA APLIKACJA GUI

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class TreningApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Asystent Treningu - Wiosłowanie Sztangą (Wersja Bazowa)")
        self.geometry("1000x700")

        self.is_running = False
        self.cap_bok = None
        self.pose_bok = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

        self.poprawne_powt = 0
        self.bledne_powt = 0
        self.cooldown_komunikatu = 0
        self.licznik_powtorzen = 0
        self.faza_ruchu = "dol"
        self.postawa_zatwierdzona = False

        self.setup_ui()
        init_db()

    def setup_ui(self):
        self.video_container = ctk.CTkFrame(self)
        self.video_container.pack(side="left", padx=20, pady=20, fill="both", expand=True)

        self.frame_bok = ctk.CTkFrame(self.video_container)
        self.frame_bok.pack(side="left", padx=10, fill="both", expand=True)
        self.lbl_tytul_bok = ctk.CTkLabel(self.frame_bok, text="Kamera: Profil (Laptop)",
                                          font=ctk.CTkFont(weight="bold"))
        self.lbl_tytul_bok.pack(pady=5)
        self.video_label_bok = ctk.CTkLabel(self.frame_bok, text="")
        self.video_label_bok.pack(expand=True)

        self.control_frame = ctk.CTkFrame(self, width=300)
        self.control_frame.pack(side="right", padx=20, pady=20, fill="y")

        self.lbl_title = ctk.CTkLabel(self.control_frame, text="Panel Kontrolny",
                                      font=ctk.CTkFont(size=20, weight="bold"))
        self.lbl_title.pack(pady=20)

        self.btn_start = ctk.CTkButton(self.control_frame, text="Rozpocznij Trening", command=self.start_trening)
        self.btn_start.pack(pady=10)

        self.btn_stop = ctk.CTkButton(self.control_frame, text="Zakończ i Zapisz", command=self.stop_trening,
                                      fg_color="red")
        self.btn_stop.pack(pady=10)

        self.btn_wykres = ctk.CTkButton(self.control_frame, text="Pokaż Historię", command=self.pokaz_wykres)
        self.btn_wykres.pack(pady=10)

        self.lbl_stats = ctk.CTkLabel(self.control_frame, text="Powtórzenia: 0 | Błędy: 0", font=ctk.CTkFont(size=16))
        self.lbl_stats.pack(pady=30)

        self.lbl_feedback_bok = ctk.CTkLabel(self.control_frame, text="Profil: Gotowy", text_color="white",
                                             font=ctk.CTkFont(size=14))
        self.lbl_feedback_bok.pack(pady=5)

    def start_trening(self):
        if not self.is_running:
            self.cap_bok = cv2.VideoCapture(0)

            self.is_running = True
            self.poprawne_powt = 0
            self.bledne_powt = 0
            self.licznik_powtorzen = 0
            self.faza_ruchu = "dol"
            self.postawa_zatwierdzona = False
            self.cooldown_komunikatu = 0

            self.lbl_stats.configure(text=f"Powtórzenia: {self.licznik_powtorzen} | Błędy: {self.bledne_powt}")
            powiedz("Rozpoczynamy trening. Ustaw się w kadrze.")
            self.aktualizuj_klatki()

    def stop_trening(self):
        if self.is_running:
            self.is_running = False
            if self.cap_bok: self.cap_bok.release()
            self.video_label_bok.configure(image='')

            if self.poprawne_powt > 0 or self.bledne_powt > 0:
                zapisz_trening(self.poprawne_powt, self.bledne_powt)
                powiedz("Trening zakończony. Wyniki zapisane.")

    def aktualizuj_klatki(self):
        if self.is_running:
            if self.cooldown_komunikatu > 0:
                self.cooldown_komunikatu -= 1

            #KAMERA BOK
            if self.cap_bok and self.cap_bok.isOpened():
                ret_bok, frame_bok = self.cap_bok.read()
                if ret_bok:
                    frame_bok_rgb = cv2.cvtColor(frame_bok, cv2.COLOR_BGR2RGB)
                    results_bok = self.pose_bok.process(frame_bok_rgb)
                    if results_bok.pose_landmarks:
                        mp_drawing.draw_landmarks(frame_bok_rgb, results_bok.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                        self.analizuj_bok(results_bok.pose_landmarks.landmark)

                    img_bok = Image.fromarray(cv2.resize(frame_bok_rgb, (640, 480)))
                    ctk_img_bok = ctk.CTkImage(light_image=img_bok, dark_image=img_bok, size=(640, 480))
                    self.video_label_bok.configure(image=ctk_img_bok)
                    self.video_label_bok.image = ctk_img_bok

            self.after(10, self.aktualizuj_klatki)

    def analizuj_bok(self, landmarks):
        # POBRANIE PUNKTÓW DO ANALIZY RUCHU
        ramie = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                 landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
        biodro = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
        kolano = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
        lokiec = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
                  landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
        nadgarstek = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,
                      landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]

        # WYLICZENIE KĄTÓW
        kat_plecow = oblicz_kat(ramie, biodro, kolano)
        kat_lokcia = oblicz_kat(ramie, lokiec, nadgarstek)

        #WERYFIKACJA POSTAWY
        if 70 < kat_plecow < 140:
            if not self.postawa_zatwierdzona:
                self.postawa_zatwierdzona = True
                self.lbl_feedback_bok.configure(text="Postawa: OK", text_color="green")
        else:
            self.postawa_zatwierdzona = False
            self.lbl_feedback_bok.configure(text="Postawa: BŁĄD", text_color="red")
            if self.cooldown_komunikatu == 0:
                powiedz("Popraw plecy!")
                self.bledne_powt += 1
                self.cooldown_komunikatu = 100

        #LOGIKA LICZENIA POWTÓRZEŃ
        if self.postawa_zatwierdzona:
            # FAZA CIĄGNIĘCIA
            if kat_lokcia < 95:
                if self.faza_ruchu == "dol":
                    self.faza_ruchu = "gora"

            # FAZA POWROTU
            elif kat_lokcia > 140:
                if self.faza_ruchu == "gora":
                    self.licznik_powtorzen += 1
                    self.poprawne_powt += 1
                    self.faza_ruchu = "dol"
                    powiedz(str(self.licznik_powtorzen))

        self.lbl_stats.configure(text=f"Powtórzenia: {self.licznik_powtorzen} | Błędy: {self.bledne_powt}")

    def pokaz_wykres(self):
        conn = sqlite3.connect('trening_db.sqlite')
        c = conn.cursor()
        c.execute("SELECT data, poprawne, bledne FROM statystyki ORDER BY id DESC LIMIT 5")
        dane = c.fetchall()
        conn.close()

        if not dane:
            powiedz("Brak danych.")
            return

        dane.reverse()
        daty = [row[0].split(" ")[0] for row in dane]
        poprawne = [row[1] for row in dane]
        bledy = [row[2] for row in dane]

        okno = ctk.CTkToplevel(self)
        okno.title("Statystyki")
        okno.geometry("600x400")

        fig, ax = plt.subplots(figsize=(5, 4))
        x = range(len(daty))
        ax.bar([i - 0.2 for i in x], poprawne, width=0.4, label='Poprawne', color='green')
        ax.bar([i + 0.2 for i in x], bledy, width=0.4, label='Błędy', color='red')
        ax.set_xticks(x)
        ax.set_xticklabels(daty)
        ax.legend()

        canvas = FigureCanvasTkAgg(fig, master=okno)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

if __name__ == "__main__":
    app = TreningApp()
    app.mainloop()