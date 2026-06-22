import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_name='trening_db.sqlite'):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS treningi (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        data TEXT
                    )''')
        c.execute('''CREATE TABLE IF NOT EXISTS serie (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        trening_id INTEGER,
                        numer_serii INTEGER,
                        poprawne INTEGER,
                        bledne INTEGER,
                        FOREIGN KEY(trening_id) REFERENCES treningi(id)
                    )''')
        conn.commit()
        conn.close()

    def nowy_trening(self):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        data_teraz = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO treningi (data) VALUES (?)", (data_teraz,))
        trening_id = c.lastrowid
        conn.commit()
        conn.close()
        return trening_id

    def zapisz_serie(self, trening_id, numer_serii, poprawne, bledne):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("INSERT INTO serie (trening_id, numer_serii, poprawne, bledne) VALUES (?, ?, ?, ?)",(trening_id, numer_serii, poprawne, bledne))
        conn.commit()
        conn.close()

    def pobierz_serie_treningu(self, trening_id):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("SELECT numer_serii, poprawne, bledne FROM serie WHERE trening_id = ? ORDER BY numer_serii ASC", (trening_id,))
        dane = c.fetchall()
        conn.close()
        return dane