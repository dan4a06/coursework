"""
database.py — Модуль для работы с базой данных SQLite.
Содержит 5 таблиц:
  1. genres       — Жанры
  2. books        — Книги (с залоговой стоимостью и стоимостью проката)
  3. readers      — Читатели
  4. rentals       — Выданные книги
  5. returns       — Факты возврата книг (финансовая история)
"""

import sqlite3
import os
from datetime import date

DB_SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS genres (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS books (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT NOT NULL,
    author          TEXT NOT NULL,
    genre_id        INTEGER REFERENCES genres(id) ON UPDATE CASCADE ON DELETE SET NULL,
    deposit         REAL NOT NULL DEFAULT 0,
    rental_price    REAL NOT NULL DEFAULT 0,
    total_copies    INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS readers (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    surname     TEXT NOT NULL,
    name        TEXT NOT NULL,
    patronymic  TEXT NOT NULL DEFAULT '',
    address     TEXT NOT NULL DEFAULT '',
    phone       TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS rentals (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id         INTEGER NOT NULL REFERENCES books(id) ON UPDATE CASCADE ON DELETE CASCADE,
    reader_id       INTEGER NOT NULL REFERENCES readers(id) ON UPDATE CASCADE ON DELETE CASCADE,
    issue_date      TEXT NOT NULL,
    expected_return TEXT NOT NULL,
    returned        INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS returns (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    rental_id   INTEGER NOT NULL REFERENCES rentals(id) ON UPDATE CASCADE ON DELETE CASCADE,
    return_date TEXT NOT NULL,
    amount_paid REAL NOT NULL DEFAULT 0
);
"""

SAMPLE_DATA = """
INSERT OR IGNORE INTO genres(name) VALUES ('Роман'),('Фантастика'),('Детектив'),('История'),('Поэзия');

INSERT OR IGNORE INTO books(title, author, genre_id, deposit, rental_price, total_copies) VALUES
  ('Мастер и Маргарита',  'Булгаков М.А.',   1, 500.0,  50.0,  2),
  ('Война и мир',         'Толстой Л.Н.',    1, 800.0,  80.0,  1),
  ('1984',                'Оруэлл Дж.',      2, 400.0,  40.0,  3),
  ('Убийство в Восточном экспрессе', 'Кристи А.', 3, 350.0, 35.0, 2),
  ('История государства Российского', 'Карамзин Н.М.', 4, 600.0, 60.0, 1);

INSERT OR IGNORE INTO readers(surname, name, patronymic, address, phone) VALUES
  ('Иванов',  'Иван',   'Иванович',    'ул. Ленина, 1',   '555-0001'),
  ('Петрова', 'Мария',  'Сергеевна',   'ул. Мира, 5',     '555-0002'),
  ('Сидоров', 'Алексей','Петрович',    'пр. Победы, 12',  '555-0003');
"""


class Database:
    def __init__(self, db_path: str = 'library.db'):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with self._connect() as conn:
            conn.executescript(DB_SCHEMA)
            # Вставляем образцы только если таблицы пусты
            cur = conn.execute("SELECT COUNT(*) FROM genres")
            if cur.fetchone()[0] == 0:
                conn.executescript(SAMPLE_DATA)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn

    # ─────────────────────────── GENRES ───────────────────────────

    def get_genres(self):
        with self._connect() as conn:
            return conn.execute("SELECT * FROM genres ORDER BY name").fetchall()

    def add_genre(self, name: str) -> int:
        with self._connect() as conn:
            cur = conn.execute("INSERT INTO genres(name) VALUES (?)", (name,))
            return cur.lastrowid

    def update_genre(self, genre_id: int, name: str):
        with self._connect() as conn:
            conn.execute("UPDATE genres SET name=? WHERE id=?", (name, genre_id))

    def delete_genre(self, genre_id: int):
        with self._connect() as conn:
            conn.execute("DELETE FROM genres WHERE id=?", (genre_id,))

    # ─────────────────────────── BOOKS ────────────────────────────

    def get_books(self):
        with self._connect() as conn:
            return conn.execute("""
                SELECT b.*, g.name AS genre_name
                FROM books b
                LEFT JOIN genres g ON b.genre_id = g.id
                ORDER BY b.title
            """).fetchall()

    def get_book(self, book_id: int):
        with self._connect() as conn:
            return conn.execute("""
                SELECT b.*, g.name AS genre_name
                FROM books b
                LEFT JOIN genres g ON b.genre_id = g.id
                WHERE b.id=?
            """, (book_id,)).fetchone()

    def add_book(self, title, author, genre_id, deposit, rental_price, total_copies=1) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO books(title,author,genre_id,deposit,rental_price,total_copies) VALUES (?,?,?,?,?,?)",
                (title, author, genre_id, deposit, rental_price, total_copies)
            )
            return cur.lastrowid

    def update_book(self, book_id, title, author, genre_id, deposit, rental_price, total_copies):
        with self._connect() as conn:
            conn.execute(
                "UPDATE books SET title=?,author=?,genre_id=?,deposit=?,rental_price=?,total_copies=? WHERE id=?",
                (title, author, genre_id, deposit, rental_price, total_copies, book_id)
            )

    def delete_book(self, book_id: int):
        with self._connect() as conn:
            conn.execute("DELETE FROM books WHERE id=?", (book_id,))

    def available_copies(self, book_id: int) -> int:
        """Количество доступных экземпляров (не выданных)."""
        with self._connect() as conn:
            total = conn.execute("SELECT total_copies FROM books WHERE id=?", (book_id,)).fetchone()
            if not total:
                return 0
            rented = conn.execute(
                "SELECT COUNT(*) FROM rentals WHERE book_id=? AND returned=0", (book_id,)
            ).fetchone()[0]
            return total[0] - rented

    # ─────────────────────────── READERS ──────────────────────────

    def get_readers(self):
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM readers ORDER BY surname, name"
            ).fetchall()

    def get_reader(self, reader_id: int):
        with self._connect() as conn:
            return conn.execute("SELECT * FROM readers WHERE id=?", (reader_id,)).fetchone()

    def add_reader(self, surname, name, patronymic, address, phone) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO readers(surname,name,patronymic,address,phone) VALUES (?,?,?,?,?)",
                (surname, name, patronymic, address, phone)
            )
            return cur.lastrowid

    def update_reader(self, reader_id, surname, name, patronymic, address, phone):
        with self._connect() as conn:
            conn.execute(
                "UPDATE readers SET surname=?,name=?,patronymic=?,address=?,phone=? WHERE id=?",
                (surname, name, patronymic, address, phone, reader_id)
            )

    def delete_reader(self, reader_id: int):
        with self._connect() as conn:
            conn.execute("DELETE FROM readers WHERE id=?", (reader_id,))

    # ─────────────────────────── RENTALS ──────────────────────────

    def get_rentals(self):
        with self._connect() as conn:
            return conn.execute("""
                SELECT r.id, b.title, rd.surname||' '||rd.name||' '||rd.patronymic AS reader_name,
                       r.issue_date, r.expected_return, r.returned,
                       b.deposit, b.rental_price, r.book_id, r.reader_id
                FROM rentals r
                JOIN books b ON r.book_id = b.id
                JOIN readers rd ON r.reader_id = rd.id
                ORDER BY r.issue_date DESC
            """).fetchall()

    def get_rental(self, rental_id: int):
        with self._connect() as conn:
            return conn.execute("""
                SELECT r.*, b.title, b.deposit, b.rental_price,
                       rd.surname||' '||rd.name||' '||rd.patronymic AS reader_name
                FROM rentals r
                JOIN books b ON r.book_id = b.id
                JOIN readers rd ON r.reader_id = rd.id
                WHERE r.id=?
            """, (rental_id,)).fetchone()

    def add_rental(self, book_id, reader_id, issue_date, expected_return) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO rentals(book_id,reader_id,issue_date,expected_return,returned) VALUES (?,?,?,?,0)",
                (book_id, reader_id, issue_date, expected_return)
            )
            return cur.lastrowid

    def delete_rental(self, rental_id: int):
        with self._connect() as conn:
            conn.execute("DELETE FROM rentals WHERE id=?", (rental_id,))

    # ─────────────────────────── RETURNS ──────────────────────────

    def get_returns(self):
        with self._connect() as conn:
            return conn.execute("""
                SELECT ret.id, b.title, rd.surname||' '||rd.name AS reader_name,
                       ren.issue_date, ret.return_date, ret.amount_paid
                FROM returns ret
                JOIN rentals ren ON ret.rental_id = ren.id
                JOIN books b ON ren.book_id = b.id
                JOIN readers rd ON ren.reader_id = rd.id
                ORDER BY ret.return_date DESC
            """).fetchall()

    def process_return(self, rental_id: int, return_date: str) -> float:
        """Фиксирует возврат книги, рассчитывает и записывает оплату."""
        with self._connect() as conn:
            rental = conn.execute(
                "SELECT * FROM rentals WHERE id=?", (rental_id,)
            ).fetchone()
            if not rental or rental['returned']:
                return 0.0
            book = conn.execute(
                "SELECT rental_price FROM books WHERE id=?", (rental['book_id'],)
            ).fetchone()
            amount = book['rental_price'] if book else 0.0
            conn.execute(
                "INSERT INTO returns(rental_id, return_date, amount_paid) VALUES (?,?,?)",
                (rental_id, return_date, amount)
            )
            conn.execute("UPDATE rentals SET returned=1 WHERE id=?", (rental_id,))
            return amount

    # ─────────────────────────── REPORTS ──────────────────────────

    def report_revenue(self):
        """Суммарная выручка по книгам."""
        with self._connect() as conn:
            return conn.execute("""
                SELECT b.title, COUNT(ret.id) AS times_rented, SUM(ret.amount_paid) AS total_income
                FROM returns ret
                JOIN rentals ren ON ret.rental_id = ren.id
                JOIN books b ON ren.book_id = b.id
                GROUP BY b.id
                ORDER BY total_income DESC
            """).fetchall()

    def report_active_rentals(self):
        """Текущие (не возвращённые) выдачи."""
        with self._connect() as conn:
            return conn.execute("""
                SELECT r.id, b.title, rd.surname||' '||rd.name AS reader,
                       r.issue_date, r.expected_return, b.deposit
                FROM rentals r
                JOIN books b ON r.book_id = b.id
                JOIN readers rd ON r.reader_id = rd.id
                WHERE r.returned = 0
                ORDER BY r.expected_return
            """).fetchall()