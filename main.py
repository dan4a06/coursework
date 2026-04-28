from __future__ import annotations
import sqlite3
import logging
from pathlib import Path
from typing import Optional, List, Any
from abc import ABC, abstractmethod

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ==================== Модели данных ====================
class General(ABC):
    def __init__(self, code: int = 0, name: str = ""):
        self._code = code
        self._name = name

    @property
    def code(self) -> int: return self._code
    @code.setter
    def code(self, v: int) -> None: self._code = v
    @property
    def name(self) -> str: return self._name
    @name.setter
    def name(self, v: str) -> None: self._name = v

class Author(General):
    def __init__(self, code: int = 0, surname: str = "", name: str = "", secname: str = ""):
        super().__init__(code, name)
        self._surname = surname
        self._secname = secname

    @property
    def surname(self) -> str: return self._surname
    @property
    def secname(self) -> str: return self._secname
    @property
    def short_name(self) -> str: return self.name[0] if self.name else ""
    @property
    def short_secname(self) -> str: return self.secname[0] if self.secname else ""

    def to_biblio_str(self) -> str:
        parts = [self.surname]
        if self.short_name: parts.append(f" {self.short_name}.")
        if self.short_secname: parts.append(f" {self.short_secname}.")
        return "".join(parts)

class Publisher(General):
    def __init__(self, code: int = 0, name: str = "", shortname: str = ""):
        super().__init__(code, name)
        self._shortname = shortname
    @property
    def shortname(self) -> str: return self._shortname

class Book(General):
    def __init__(self, code: int = 0, name: str = "", img: str = "",
                 publisher: Optional[Publisher] = None, year: int = 0, pages: int = 0):
        super().__init__(code, name)
        self._authors: List[Author] = []
        self._img = img
        self._publisher = publisher
        self.pages = pages
        self.year = year

    @property
    def publisher(self) -> Optional[Publisher]: return self._publisher
    @publisher.setter
    def publisher(self, v: Optional[Publisher]) -> None: self._publisher = v

    @property
    def pages(self) -> int: return self._pages
    @pages.setter
    def pages(self, v: int) -> None:
        if v <= 0: raise ValueError("Страниц должно быть > 0")
        self._pages = v

    @property
    def year(self) -> int: return self._year
    @year.setter
    def year(self, v: int) -> None:
        if not (1000 <= v <= 9999): raise ValueError("Некоректный год")
        self._year = v

    def add_author(self, author: Author) -> None:
        if author not in self._authors: self._authors.append(author)
    def remove_author(self, author: Author) -> None:
        self._authors = [a for a in self._authors if a is not author]
    def clear_authors(self) -> None: self._authors.clear()

    @property
    def author_biblio(self) -> str:
        return ", ".join(a.to_biblio_str() for a in self._authors)

    def to_biblio_str(self) -> str:
        publ = self._publisher.shortname if self._publisher else "Без издательства"
        return f"{self.author_biblio} {self.name} - {publ}, {self._year}. - {self._pages} с."

    def __str__(self) -> str: return self.to_biblio_str()

# ==================== Менеджер библиотеки ====================
class Library:
    def __init__(self):
        self.authors: List[Author] = []
        self.publishers: List[Publisher] = []
        self.books: List[Book] = []

    def _next_code(self, collection: List[Any]) -> int:
        return max((item.code for item in collection), default=0) + 1

    def find_by_code(self, collection: List[Any], code: int) -> Optional[Any]:
        return next((item for item in collection if item.code == code), None)
    #next(..., None) → возвращает первый найденный объект. Если генератор пуст (совпадений нет), возвращает None.
    '''
    def find_by_code_old(self, collection, code):
    for item in collection:           1. Перебираем всё подряд
        if item.code == code:         2. Проверяем условие
            return item               3. Нашли → сразу выходим из функции
    return None                       4. Не нашли → возвращаем None
    '''

    def add_author(self, surname: str, name: str = "", secname: str = "") -> Author:
        a = Author(self._next_code(self.authors), surname, name, secname)
        self.authors.append(a)
        return a

    def add_publisher(self, name: str, shortname: str = "") -> Publisher:
        p = Publisher(self._next_code(self.publishers), name, shortname)
        self.publishers.append(p)
        return p

    def add_book(self, name: str, publisher: Optional[Publisher] = None,
                 year: int = 0, pages: int = 0, img: str = "") -> Book:
        b = Book(self._next_code(self.books), name, img, publisher, year, pages)
        self.books.append(b)
        return b

    def clear(self) -> None:
        self.authors.clear()
        self.publishers.clear()
        self.books.clear()

# ==================== Абстрактный интерфейс данных ====================
class DataStorage(ABC):
    def __init__(self, library: Library, db_path: Path):
        self.library = library
        self.db_path = db_path
        self._init_db()

    @abstractmethod
    def read(self) -> None: ...
    @abstractmethod
    def write(self) -> None: ...
    @abstractmethod
    def _init_db(self) -> None: ...

# ==================== Реализация SQLite ====================
class SQLiteStorage(DataStorage):
    SCHEMA = """
    PRAGMA foreign_keys = ON;
    CREATE TABLE IF NOT EXISTS author (code INTEGER PRIMARY KEY, surname TEXT, name TEXT, secname TEXT);
    CREATE TABLE IF NOT EXISTS publisher (code INTEGER PRIMARY KEY, name TEXT, shortname TEXT);
    CREATE TABLE IF NOT EXISTS book (code INTEGER PRIMARY KEY, name TEXT, img TEXT, year INTEGER, pages INTEGER, publ_code INTEGER REFERENCES publisher(code) ON DELETE SET NULL);
    CREATE TABLE IF NOT EXISTS book_author (book_code INTEGER, author_code INTEGER, PRIMARY KEY(book_code, author_code), FOREIGN KEY(book_code) REFERENCES book(code) ON DELETE CASCADE, FOREIGN KEY(author_code) REFERENCES author(code) ON DELETE CASCADE);
    """

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(self.SCHEMA)

    def read(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            cur.execute("SELECT * FROM author")
            for r in cur.fetchall():
                a = Author(r["code"], r["surname"], r["name"], r["secname"])
                self.library.authors.append(a)

            cur.execute("SELECT * FROM publisher")
            for r in cur.fetchall():
                p = Publisher(r["code"], r["name"], r["shortname"])
                self.library.publishers.append(p)

            pub_dict = {p.code: p for p in self.library.publishers}
            cur.execute("SELECT * FROM book")
            for r in cur.fetchall():
                publ = pub_dict.get(r["publ_code"])
                b = Book(r["code"], r["name"], r["img"], publ, r["year"], r["pages"])
                self.library.books.append(b)

            book_dict = {b.code: b for b in self.library.books}
            author_dict = {a.code: a for a in self.library.authors}
            cur.execute("SELECT book_code, author_code FROM book_author")
            for r in cur.fetchall():
                book = book_dict.get(r["book_code"])
                author = author_dict.get(r["author_code"])
                if book and author: book.add_author(author)

        logger.info(f"✅ Загружено {len(self.library.authors)} авторов, {len(self.library.publishers)} издательств, {len(self.library.books)} книг")

    def write(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.executescript("PRAGMA foreign_keys = ON; DELETE FROM book_author; DELETE FROM book; DELETE FROM publisher; DELETE FROM author;")

            for a in self.library.authors:
                cur.execute("INSERT INTO author VALUES (?,?,?,?)", (a.code, a.surname, a.name, a.secname))
            for p in self.library.publishers:
                cur.execute("INSERT INTO publisher VALUES (?,?,?)", (p.code, p.name, p.shortname))
            for b in self.library.books:
                publ_code = b.publisher.code if b.publisher else None
                cur.execute("INSERT INTO book VALUES (?,?,?,?,?,?)", (b.code, b.name, b._img, b.year, b.pages, publ_code))
                for a in b._authors:
                    cur.execute("INSERT INTO book_author VALUES (?,?)", (b.code, a.code))
        logger.info(f"✅ Данные успешно записаны в {self.db_path}")

# ==================== Демонстрация ====================
if __name__ == "__main__":
    # DB_FILE = Path("library_modern.db")

    # lib = Library()
    # a1 = lib.add_author("Хорн", "Роджер")
    # a2 = lib.add_author("Джонсон", "Чарльз")
    # p1 = lib.add_publisher('Москва "Мир"', "М.: Мир")
    # b1 = lib.add_book("Матричный анализ", p1, 1989, 655)
    # b1.add_author(a1)
    # b1.add_author(a2)

    # storage = SQLiteStorage(lib, DB_FILE)
    # storage.write()

    # lib2 = Library()
    # storage2 = SQLiteStorage(lib2, DB_FILE)
    # storage2.read()

    # print("\n📚 Библиографический список из БД:")
    # for book in lib2.books:
    #     print(book)
        
    a = Author(1, "Афанасьев", "Даниил", "Алексеевич")
    print(a.to_biblio_str())