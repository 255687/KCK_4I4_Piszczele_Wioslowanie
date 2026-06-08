import customtkinter as ctk

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class MenuApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Asystent Treningu - Menu Główne")
        self.geometry("400x500")

        self.setup_ui()

    def setup_ui(self):
        self.lbl_main_title = ctk.CTkLabel(self, text="Asystent Wiosłowania", font=ctk.CTkFont(size=24, weight="bold"))
        self.lbl_main_title.pack(pady=40)

        self.btn_przejdz_do_treningu = ctk.CTkButton(self, text="Przejdź do Treningu", width=250, height=45, font=ctk.CTkFont(size=15))
        self.btn_przejdz_do_treningu.pack(pady=15)

        self.btn_wyswietl_wykres = ctk.CTkButton(self, text="Wyświetl Ostatni Wykres", width=250, height=45, font=ctk.CTkFont(size=15))
        self.btn_wyswietl_wykres.pack(pady=15)

        self.btn_wejdz_w_baze = ctk.CTkButton(self, text="Wejdź w Bazę Danych", width=250, height=45, font=ctk.CTkFont(size=15))
        self.btn_wejdz_w_baze.pack(pady=15)

if __name__ == "__main__":
    app = MenuApp()
    app.mainloop()