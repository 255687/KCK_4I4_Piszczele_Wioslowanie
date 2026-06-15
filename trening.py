import cv2
import mediapipe as mp
import customtkinter as ctk
import math
from PIL import Image
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from database import Database
from voice import VoiceAssistant


def oblicz_kat(p1, p2, p3):
    kat = math.degrees(math.atan2(p3[1] - p2[1], p3[0] - p2[0]) - math.atan2(p1[1] - p2[1], p1[0] - p2[0]))
    kat = abs(kat)
    if kat > 180.0:
        kat = 360.0 - kat
    return kat


ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class TreningApp(ctk.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Asystent Treningu - Wiosłowanie Sztangą (PRO - 2 Kamery)")
        self.geometry("1400x700")

        self.db = Database()
        self.voice = VoiceAssistant()

        self.is_running = False
        self.system_aktywny = False
        self.cap_bok = None
        self.cap_tyl = None

        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils

        self.pose_bok = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.pose_tyl = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

        self.poprawne_powt = 0
        self.bledne_powt = 0
        self.cooldown_komunikatu = 0
        self.licznik_powtorzen = 0
        self.faza_ruchu = "dol"
        self.postawa_zatwierdzona = False
        self.odliczanie_trwa = False
        self.current_trening_id = None
        self.numer_serii = 1

        self.setup_ui()

    def setup_ui(self):
        self.video_container = ctk.CTkFrame(self)
        self.video_container.pack(side="left", padx=20, pady=20, fill="both", expand=True)

        self.frame_bok = ctk.CTkFrame(self.video_container)
        self.frame_bok.pack(side="left", padx=10, fill="both", expand=True)
        self.lbl_tytul_bok = ctk.CTkLabel(self.frame_bok, text="Kamera: Profil (Laptop)",font=ctk.CTkFont(weight="bold"))
        self.lbl_tytul_bok.pack(pady=5)
        self.video_label_bok = ctk.CTkLabel(self.frame_bok, text="")
        self.video_label_bok.pack(expand=True)

        self.frame_tyl = ctk.CTkFrame(self.video_container)
        self.frame_tyl.pack(side="left", padx=10, fill="both", expand=True)
        self.lbl_tytul_tyl = ctk.CTkLabel(self.frame_tyl, text="Kamera: Tył (iPhone)", font=ctk.CTkFont(weight="bold"))
        self.lbl_tytul_tyl.pack(pady=5)
        self.video_label_tyl = ctk.CTkLabel(self.frame_tyl, text="")
        self.video_label_tyl.pack(expand=True)

        self.control_frame = ctk.CTkFrame(self, width=300)
        self.control_frame.pack(side="right", padx=20, pady=20, fill="y")

        self.lbl_title = ctk.CTkLabel(self.control_frame, text="Panel Kontrolny",font=ctk.CTkFont(size=20, weight="bold"))
        self.lbl_title.pack(pady=20)

        self.btn_start = ctk.CTkButton(self.control_frame, text="Rozpocznij Trening", command=self.start_trening)
        self.btn_start.pack(pady=10)

        self.btn_stop = ctk.CTkButton(self.control_frame, text="Zakończ i Zapisz", command=self.stop_trening,fg_color="red")
        self.btn_stop.pack(pady=10)

        self.btn_wykres = ctk.CTkButton(self.control_frame, text="Pokaż Historię", command=self.pokaz_wykres)
        self.btn_wykres.pack(pady=10)

        self.lbl_stats = ctk.CTkLabel(self.control_frame, text="Seria: 1 | Powtórzenia: 0 | Błędy: 0", font=ctk.CTkFont(size=16))
        self.lbl_stats.pack(pady=30)

        self.lbl_feedback_bok = ctk.CTkLabel(self.control_frame, text="Profil: Gotowy", text_color="white",font=ctk.CTkFont(size=14))
        self.lbl_feedback_bok.pack(pady=5)

        self.lbl_feedback_tyl = ctk.CTkLabel(self.control_frame, text="Symetria: Gotowa", text_color="white",font=ctk.CTkFont(size=14))
        self.lbl_feedback_tyl.pack(pady=5)

    def start_trening(self):
        if not self.is_running:
            self.cap_bok = cv2.VideoCapture(0)

            ADRES_IP_TELEFONU = 1
            self.cap_tyl = cv2.VideoCapture(ADRES_IP_TELEFONU)

            self.is_running = True
            self.system_aktywny = False
            self.current_trening_id = self.db.nowy_trening()
            self.numer_serii = 1
            self.poprawne_powt = 0
            self.bledne_powt = 0
            self.licznik_powtorzen = 0
            self.faza_ruchu = "dol"
            self.postawa_zatwierdzona = False
            self.cooldown_komunikatu = 0
            self.odliczanie_trwa = False

            self.lbl_stats.configure(text=f"Seria: {self.numer_serii} | Powtórzenia: {self.licznik_powtorzen} | Błędy: {self.bledne_powt}")

            self.voice.powiedz("Trening rozpoczęty. Lewa ręka startuje serię. Prawa kończy serię. Obie ręce kończą trening.")
            self.aktualizuj_klatki()

    def stop_trening(self):
        if self.is_running:
            if self.system_aktywny and (self.poprawne_powt > 0 or self.bledne_powt > 0):
                self.zakoncz_serie()

            self.is_running = False
            if self.cap_bok: self.cap_bok.release()
            if self.cap_tyl: self.cap_tyl.release()

            self.video_label_bok.configure(image=None)
            self.video_label_tyl.configure(image=None)

            self.voice.powiedz("Trening zakończony.")
            self.after(100, self.pokaz_wykres)

    def aktualizuj_klatki(self):
        if self.is_running:
            if self.cooldown_komunikatu > 0:
                self.cooldown_komunikatu -= 1

            if self.cap_bok and self.cap_bok.isOpened():
                ret_bok, frame_bok = self.cap_bok.read()
                if ret_bok:
                    frame_bok_rgb = cv2.cvtColor(frame_bok, cv2.COLOR_BGR2RGB)
                    results_bok = self.pose_bok.process(frame_bok_rgb)
                    if results_bok.pose_landmarks:
                        self.mp_drawing.draw_landmarks(frame_bok_rgb, results_bok.pose_landmarks,
                                                       self.mp_pose.POSE_CONNECTIONS)
                        self.analizuj_bok(results_bok.pose_landmarks.landmark)

                    img_bok = Image.fromarray(cv2.resize(frame_bok_rgb, (480, 360)))
                    ctk_img_bok = ctk.CTkImage(light_image=img_bok, dark_image=img_bok, size=(480, 360))
                    self.video_label_bok.configure(image=ctk_img_bok)
                    self.video_label_bok.image = ctk_img_bok

            if self.cap_tyl and self.cap_tyl.isOpened():
                ret_tyl, frame_tyl = self.cap_tyl.read()
                if ret_tyl:
                    frame_tyl_rgb = cv2.cvtColor(frame_tyl, cv2.COLOR_BGR2RGB)
                    results_tyl = self.pose_tyl.process(frame_tyl_rgb)
                    if results_tyl.pose_landmarks:
                        self.mp_drawing.draw_landmarks(frame_tyl_rgb, results_tyl.pose_landmarks,
                                                       self.mp_pose.POSE_CONNECTIONS)
                        if self.system_aktywny:
                            self.analizuj_tyl(results_tyl.pose_landmarks.landmark)

                    img_tyl = Image.fromarray(cv2.resize(frame_tyl_rgb, (480, 360)))
                    ctk_img_tyl = ctk.CTkImage(light_image=img_tyl, dark_image=img_tyl, size=(480, 360))
                    self.video_label_tyl.configure(image=ctk_img_tyl)
                    self.video_label_tyl.image = ctk_img_tyl

            self.after(10, self.aktualizuj_klatki)

    def rozpocznij_odliczanie(self, sekundy):
        self.odliczanie_trwa = True
        self.voice.powiedz(f"Seria {self.numer_serii} rozpocznie się za {sekundy} sekund. Ustaw się.")
        self.odliczanie_krok(sekundy)

    def odliczanie_krok(self, sekundy):
        if not self.is_running:
            return

        if sekundy > 0:
            self.lbl_feedback_bok.configure(text=f"Start za: {sekundy} s", text_color="orange")
            self.after(1000, lambda: self.odliczanie_krok(sekundy - 1))
        else:
            self.odliczanie_trwa = False
            self.system_aktywny = True
            self.lbl_feedback_bok.configure(text="STATUS: AKTYWNY", text_color="cyan")
            self.voice.powiedz("Start!")

    def zakoncz_serie(self):
        self.db.zapisz_serie(self.current_trening_id, self.numer_serii, self.poprawne_powt, self.bledne_powt)
        self.voice.powiedz(f"Seria {self.numer_serii} zakończona i zapisana.")
        self.numer_serii += 1
        self.poprawne_powt = 0
        self.bledne_powt = 0
        self.licznik_powtorzen = 0
        self.faza_ruchu = "dol"
        self.postawa_zatwierdzona = False
        self.system_aktywny = False
        self.lbl_stats.configure(text=f"Seria: {self.numer_serii} | Powtórzenia: 0 | Błędy: 0")

    def analizuj_bok(self, landmarks):
        lewa_dlon_y = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value].y
        lewe_oko_y = landmarks[self.mp_pose.PoseLandmark.LEFT_EYE.value].y

        prawa_dlon_y = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value].y
        prawe_oko_y = landmarks[self.mp_pose.PoseLandmark.RIGHT_EYE.value].y

        lewa_w_gorze = lewa_dlon_y < lewe_oko_y
        prawa_w_gorze = prawa_dlon_y < prawe_oko_y

        if lewa_w_gorze and prawa_w_gorze:
            self.after(0, self.stop_trening)
            return

        if self.system_aktywny:
            if prawa_w_gorze and not lewa_w_gorze:
                self.zakoncz_serie()
                return

        if not self.system_aktywny:
            if not self.odliczanie_trwa:
                if lewa_w_gorze and not prawa_w_gorze:
                    self.rozpocznij_odliczanie(5)
                else:
                    self.lbl_feedback_bok.configure(text=f"Podnieś lewą rękę (Start Serii {self.numer_serii})", text_color="yellow")
            return

        ramie = [landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                 landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
        biodro = [landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value].x,
                  landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value].y]
        kolano = [landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                  landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value].y]
        lokiec = [landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
                  landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
        nadgarstek = [landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value].x,
                      landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value].y]

        kat_plecow = oblicz_kat(ramie, biodro, kolano)
        kat_lokcia = oblicz_kat(ramie, lokiec, nadgarstek)

        if 70 < kat_plecow < 140:
            if not self.postawa_zatwierdzona:
                self.postawa_zatwierdzona = True
                self.lbl_feedback_bok.configure(text="Postawa: OK", text_color="green")
        else:
            self.postawa_zatwierdzona = False
            self.lbl_feedback_bok.configure(text="Postawa: BŁĄD", text_color="red")
            if self.cooldown_komunikatu == 0:
                self.voice.powiedz("Popraw plecy!")
                self.bledne_powt += 1
                self.cooldown_komunikatu = 100

        if self.postawa_zatwierdzona:
            if kat_lokcia < 95:
                if self.faza_ruchu == "dol":
                    self.faza_ruchu = "gora"
            elif kat_lokcia > 140:
                if self.faza_ruchu == "gora":
                    self.licznik_powtorzen += 1
                    self.poprawne_powt += 1
                    self.faza_ruchu = "dol"
                    self.voice.powiedz(str(self.licznik_powtorzen))

        self.lbl_stats.configure(text=f"Seria: {self.numer_serii} | Powtórzenia: {self.licznik_powtorzen} | Błędy: {self.bledne_powt}")

    def analizuj_tyl(self, landmarks):
        lewy_bark_y = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].y
        prawy_bark_y = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y
        roznica_barkow = abs(lewy_bark_y - prawy_bark_y)

        lewy_lokiec_y = landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value].y
        prawy_lokiec_y = landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW.value].y
        roznica_lokci = abs(lewy_lokiec_y - prawy_lokiec_y)

        if self.faza_ruchu == "gora":
            blad_barkow = roznica_barkow > 0.05
            blad_lokci = roznica_lokci > 0.08

            if blad_barkow or blad_lokci:
                self.lbl_feedback_tyl.configure(text="Symetria: ZŁA", text_color="red")
                if self.cooldown_komunikatu == 0:
                    if blad_barkow and blad_lokci:
                        self.voice.powiedz("Nierówne barki i łokcie.")
                    elif blad_barkow:
                        self.voice.powiedz("Wyrównaj barki.")
                    elif blad_lokci:
                        self.voice.powiedz("Nierówne łokcie, ciągnij symetrycznie.")

                    self.bledne_powt += 1
                    self.cooldown_komunikatu = 100
            else:
                self.lbl_feedback_tyl.configure(text="Symetria: OK", text_color="green")
        else:
            self.lbl_feedback_tyl.configure(text="Symetria: (w spoczynku)", text_color="white")

    def pokaz_wykres(self):
        if not self.current_trening_id:
            return

        dane = self.db.pobierz_serie_treningu(self.current_trening_id)

        if not dane:
            self.voice.powiedz("Brak danych dla tego treningu.")
            return

        serie_labels = [f"Seria {row[0]}" for row in dane]
        poprawne = [row[1] for row in dane]
        bledy = [row[2] for row in dane]

        okno = ctk.CTkToplevel(self)
        okno.title("Statystyki Bieżącego Treningu")
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