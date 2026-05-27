import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_name='trening_db.sqlite'):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS statystyki (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        data TEXT,
                        poprawne INTEGER,
                        bledne INTEGER
                    )''')
        conn.commit()
        conn.close()

    def zapisz_trening(self, poprawne, bledne):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("INSERT INTO statystyki (data, poprawne, bledne) VALUES (?, ?, ?)",
                  (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), poprawne, bledne))
        conn.commit()
        conn.close()

    def pobierz_statystyki(self, limit=5):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("SELECT data, poprawne, bledne FROM statystyki ORDER BY id DESC LIMIT ?", (limit,))
        dane = c.fetchall()
        conn.close()
        return dane