"""Работа с базой данных SQLite.

Таблицы:
    genres   — жанры
    authors  — авторы
    books    — книги (ссылаются на авторов и жанры)
    readings — журнал чтения (сколько страниц прочитано в какой день)
    settings — настройки (например, цель на год)
"""
import csv
import datetime
import sqlite3

STATUSES = ["Хочу прочитать", "Читаю", "Прочитано"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS genres (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS authors (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL UNIQUE,
    country    TEXT DEFAULT '',
    birth_year INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS books (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    title     TEXT NOT NULL,
    author_id INTEGER REFERENCES authors(id) ON DELETE SET NULL,
    genre_id  INTEGER REFERENCES genres(id) ON DELETE SET NULL,
    year      INTEGER DEFAULT 0,
    pages     INTEGER DEFAULT 0,
    rating    INTEGER DEFAULT 0,
    status    TEXT DEFAULT 'Хочу прочитать',
    favorite  INTEGER DEFAULT 0,
    cover     TEXT DEFAULT '',
    notes     TEXT DEFAULT '',
    added     TEXT
);
CREATE TABLE IF NOT EXISTS readings (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    date    TEXT NOT NULL,
    pages   INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""

CSV_FIELDS = ["title", "author", "genre", "year", "pages", "rating",
              "status", "favorite", "notes"]


class Database:
    def __init__(self, path):
        self.con = sqlite3.connect(path)
        self.con.row_factory = sqlite3.Row
        self.con.execute("PRAGMA foreign_keys = ON")
        self.con.executescript(SCHEMA)
        self.con.commit()

    def close(self):
        self.con.close()

    def is_empty(self):
        return self.con.execute("SELECT COUNT(*) FROM books").fetchone()[0] == 0

    # ---------------------------------------------------------------- жанры
    def genres(self):
        return self.con.execute(
            "SELECT g.id, g.name, COUNT(b.id) AS cnt FROM genres g "
            "LEFT JOIN books b ON b.genre_id = g.id "
            "GROUP BY g.id ORDER BY g.name").fetchall()

    def add_genre(self, name):
        cur = self.con.execute("INSERT INTO genres(name) VALUES (?)", (name,))
        self.con.commit()
        return cur.lastrowid

    def rename_genre(self, genre_id, name):
        self.con.execute("UPDATE genres SET name = ? WHERE id = ?", (name, genre_id))
        self.con.commit()

    def delete_genre(self, genre_id):
        self.con.execute("DELETE FROM genres WHERE id = ?", (genre_id,))
        self.con.commit()

    def genre_id(self, name, create=True):
        name = (name or "").strip()
        if not name:
            return None
        row = self.con.execute("SELECT id FROM genres WHERE name = ?", (name,)).fetchone()
        if row:
            return row["id"]
        return self.add_genre(name) if create else None

    # --------------------------------------------------------------- авторы
    def authors(self):
        return self.con.execute(
            "SELECT a.id, a.name, a.country, a.birth_year, COUNT(b.id) AS cnt "
            "FROM authors a LEFT JOIN books b ON b.author_id = a.id "
            "GROUP BY a.id ORDER BY a.name").fetchall()

    def add_author(self, name, country="", birth_year=0):
        cur = self.con.execute(
            "INSERT INTO authors(name, country, birth_year) VALUES (?, ?, ?)",
            (name, country, birth_year))
        self.con.commit()
        return cur.lastrowid

    def update_author(self, author_id, name, country, birth_year):
        self.con.execute(
            "UPDATE authors SET name = ?, country = ?, birth_year = ? WHERE id = ?",
            (name, country, birth_year, author_id))
        self.con.commit()

    def delete_author(self, author_id):
        self.con.execute("DELETE FROM authors WHERE id = ?", (author_id,))
        self.con.commit()

    def author_id(self, name, create=True):
        name = (name or "").strip()
        if not name:
            return None
        row = self.con.execute("SELECT id FROM authors WHERE name = ?", (name,)).fetchone()
        if row:
            return row["id"]
        return self.add_author(name) if create else None

    # ---------------------------------------------------------------- книги
    BOOK_SELECT = (
        "SELECT b.*, IFNULL(a.name, '') AS author, IFNULL(g.name, '') AS genre, "
        "IFNULL((SELECT SUM(r.pages) FROM readings r WHERE r.book_id = b.id), 0) AS read_pages "
        "FROM books b "
        "LEFT JOIN authors a ON a.id = b.author_id "
        "LEFT JOIN genres g ON g.id = b.genre_id ")

    def books(self, text="", genre_id=None, status=None, favorites=False):
        where, params = [], []
        if text:
            where.append("(b.title LIKE ? OR a.name LIKE ?)")
            params += [f"%{text}%", f"%{text}%"]
        if genre_id:
            where.append("b.genre_id = ?")
            params.append(genre_id)
        if status:
            where.append("b.status = ?")
            params.append(status)
        if favorites:
            where.append("b.favorite = 1")
        sql = self.BOOK_SELECT
        if where:
            sql += "WHERE " + " AND ".join(where) + " "
        sql += "ORDER BY b.title"
        return self.con.execute(sql, params).fetchall()

    def book(self, book_id):
        return self.con.execute(self.BOOK_SELECT + "WHERE b.id = ?", (book_id,)).fetchone()

    def add_book(self, data):
        data = dict(data)
        data.setdefault("added", datetime.date.today().isoformat())
        cur = self.con.execute(
            "INSERT INTO books(title, author_id, genre_id, year, pages, rating, "
            "status, favorite, cover, notes, added) "
            "VALUES (:title, :author_id, :genre_id, :year, :pages, :rating, "
            ":status, :favorite, :cover, :notes, :added)", data)
        self.con.commit()
        return cur.lastrowid

    def update_book(self, book_id, data):
        data = dict(data, id=book_id)
        self.con.execute(
            "UPDATE books SET title = :title, author_id = :author_id, "
            "genre_id = :genre_id, year = :year, pages = :pages, rating = :rating, "
            "status = :status, favorite = :favorite, cover = :cover, notes = :notes "
            "WHERE id = :id", data)
        self.con.commit()

    def set_status(self, book_id, status):
        self.con.execute("UPDATE books SET status = ? WHERE id = ?", (status, book_id))
        self.con.commit()

    def set_favorite(self, book_id, favorite):
        self.con.execute("UPDATE books SET favorite = ? WHERE id = ?",
                         (int(favorite), book_id))
        self.con.commit()

    def delete_book(self, book_id):
        self.con.execute("DELETE FROM books WHERE id = ?", (book_id,))
        self.con.commit()

    # --------------------------------------------------------- журнал чтения
    def readings(self, book_id=None, date=None):
        sql = ("SELECT r.id, r.date, r.pages, r.book_id, b.title FROM readings r "
               "JOIN books b ON b.id = r.book_id ")
        where, params = [], []
        if book_id is not None:
            where.append("r.book_id = ?")
            params.append(book_id)
        if date is not None:
            where.append("r.date = ?")
            params.append(date)
        if where:
            sql += "WHERE " + " AND ".join(where) + " "
        sql += "ORDER BY r.date DESC, r.id DESC"
        return self.con.execute(sql, params).fetchall()

    def reading_dates(self):
        return [r[0] for r in self.con.execute("SELECT DISTINCT date FROM readings")]

    def add_reading(self, book_id, date, pages):
        self.con.execute("INSERT INTO readings(book_id, date, pages) VALUES (?, ?, ?)",
                         (book_id, date, pages))
        self.con.commit()

    def delete_reading(self, reading_id):
        self.con.execute("DELETE FROM readings WHERE id = ?", (reading_id,))
        self.con.commit()

    # ------------------------------------------------------------ статистика
    def count_by_status(self):
        result = {s: 0 for s in STATUSES}
        for row in self.con.execute("SELECT status, COUNT(*) FROM books GROUP BY status"):
            result[row[0]] = row[1]
        return result

    def count_by_genre(self):
        return [(r[0], r[1]) for r in self.con.execute(
            "SELECT IFNULL(g.name, 'Без жанра'), COUNT(*) FROM books b "
            "LEFT JOIN genres g ON g.id = b.genre_id GROUP BY b.genre_id "
            "ORDER BY COUNT(*) DESC")]

    def pages_read_total(self, year=None):
        if year:
            row = self.con.execute(
                "SELECT IFNULL(SUM(pages), 0) FROM readings WHERE date LIKE ?",
                (f"{year}-%",)).fetchone()
        else:
            row = self.con.execute("SELECT IFNULL(SUM(pages), 0) FROM readings").fetchone()
        return row[0]

    def pages_by_month(self, year):
        result = [0] * 12
        for row in self.con.execute(
                "SELECT CAST(substr(date, 6, 2) AS INTEGER), SUM(pages) FROM readings "
                "WHERE date LIKE ? GROUP BY substr(date, 6, 2)", (f"{year}-%",)):
            result[row[0] - 1] = row[1]
        return result

    # ------------------------------------------------------------- настройки
    def setting(self, key, default=None):
        row = self.con.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row[0] if row else default

    def set_setting(self, key, value):
        self.con.execute("INSERT OR REPLACE INTO settings(key, value) VALUES (?, ?)",
                         (key, str(value)))
        self.con.commit()

    # -------------------------------------------------------------- CSV
    def import_csv(self, path):
        """Добавляет книги из CSV-файла. Возвращает число добавленных книг."""
        count = 0
        with open(path, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f, delimiter=";"):
                title = (row.get("title") or "").strip()
                if not title:
                    continue
                status = row.get("status") or STATUSES[0]
                self.add_book({
                    "title": title,
                    "author_id": self.author_id(row.get("author")),
                    "genre_id": self.genre_id(row.get("genre")),
                    "year": _int(row.get("year")),
                    "pages": _int(row.get("pages")),
                    "rating": max(0, min(5, _int(row.get("rating")))),
                    "status": status if status in STATUSES else STATUSES[0],
                    "favorite": 1 if _int(row.get("favorite")) else 0,
                    "cover": "",
                    "notes": row.get("notes") or "",
                })
                count += 1
        return count

    def export_csv(self, path, books=None):
        books = self.books() if books is None else books
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(CSV_FIELDS)
            for b in books:
                writer.writerow([b[name] for name in CSV_FIELDS])
        return len(books)


def _int(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0
