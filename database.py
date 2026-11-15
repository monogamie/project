"""Работа с базой данных SQLite (уроки QT 6, QT 7 и QT 8).

Все SQL-запросы программы собраны в этом файле.
Окна сами не пишут SQL, а вызывают методы класса LibraryDB.
"""
import csv
import sqlite3

# Файл базы данных создаётся рядом с программой
DB_NAME = "library.sqlite"

# Возможные статусы книги
STATUSES = ["Хочу прочитать", "Читаю", "Прочитано"]

# Заголовки столбцов в CSV-файле
CSV_HEADER = ["title", "author", "genre", "year", "pages",
              "rating", "status", "favorite", "notes"]

# Варианты сортировки: подпись в списке и часть SQL-запроса ORDER BY
SORT_ORDERS = {
    "По названию": "books.title",
    "По автору": "authors.name, books.title",
    "По году": "books.year DESC",
    "По оценке": "books.rating DESC, books.title",
}

# Общая часть запроса книг: к книге присоединяем автора и жанр,
# а подзапросом считаем, сколько страниц прочитано по журналу
BOOKS_QUERY = """
    SELECT books.id, books.title, books.author_id, books.genre_id,
           authors.name AS author, genres.title AS genre,
           books.year, books.pages, books.rating, books.status,
           books.favorite, books.cover, books.notes, books.added,
           (SELECT SUM(readings.pages) FROM readings
            WHERE readings.book_id = books.id) AS read_pages
    FROM books
    LEFT JOIN authors ON authors.id = books.author_id
    LEFT JOIN genres ON genres.id = books.genre_id
"""


def to_int(text):
    """Превращает строку в число, а если это не число, возвращает 0."""
    text = text.strip()
    if text.isdigit():
        return int(text)
    return 0


class LibraryDB:
    """База данных библиотеки: книги, авторы, жанры, журнал, настройки."""

    def __init__(self, db_name=DB_NAME):
        # Подключаемся один раз при запуске (файл создастся сам)
        self.con = sqlite3.connect(db_name)
        # Обращение к полям по имени: book["title"] (урок QT 6)
        self.con.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        """Создаёт таблицы, если их ещё нет (урок QT 8)."""
        cur = self.con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS authors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS genres (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL UNIQUE
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author_id INTEGER,
                genre_id INTEGER,
                year INTEGER,
                pages INTEGER,
                rating INTEGER,
                status TEXT,
                favorite INTEGER,
                cover TEXT,
                notes TEXT,
                added TEXT,
                FOREIGN KEY (author_id) REFERENCES authors(id),
                FOREIGN KEY (genre_id) REFERENCES genres(id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                pages INTEGER NOT NULL,
                FOREIGN KEY (book_id) REFERENCES books(id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                name TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        self.con.commit()

    def close(self):
        self.con.close()

    def books_count(self):
        cur = self.con.cursor()
        return cur.execute("SELECT COUNT(*) FROM books").fetchone()[0]

    # ------------------------------------------------------------ авторы
    def get_authors(self):
        """Все авторы и число их книг (LEFT JOIN + GROUP BY, урок QT 7)."""
        cur = self.con.cursor()
        return cur.execute("""
            SELECT authors.id, authors.name, COUNT(books.id) AS books
            FROM authors
            LEFT JOIN books ON books.author_id = authors.id
            GROUP BY authors.id
            ORDER BY authors.name
        """).fetchall()

    def find_author_id(self, name):
        cur = self.con.cursor()
        row = cur.execute("SELECT id FROM authors WHERE name = ?",
                          (name,)).fetchone()
        if row:
            return row["id"]
        return None

    def add_author(self, name):
        """Добавляет автора, если такого ещё нет, и возвращает его id."""
        name = name.strip()
        if not name:
            return None
        if self.find_author_id(name) is None:
            cur = self.con.cursor()
            cur.execute("INSERT INTO authors(name) VALUES(?)", (name,))
            self.con.commit()
        return self.find_author_id(name)

    def rename_author(self, author_id, name):
        cur = self.con.cursor()
        cur.execute("UPDATE authors SET name = ? WHERE id = ?",
                    (name, author_id))
        self.con.commit()

    def delete_author(self, author_id):
        """Удаляет автора. У его книг автор станет «не указан»."""
        cur = self.con.cursor()
        cur.execute("UPDATE books SET author_id = NULL WHERE author_id = ?",
                    (author_id,))
        cur.execute("DELETE FROM authors WHERE id = ?", (author_id,))
        self.con.commit()

    # ------------------------------------------------------------- жанры
    def get_genres(self):
        """Все жанры и число книг в каждом."""
        cur = self.con.cursor()
        return cur.execute("""
            SELECT genres.id, genres.title, COUNT(books.id) AS books
            FROM genres
            LEFT JOIN books ON books.genre_id = genres.id
            GROUP BY genres.id
            ORDER BY genres.title
        """).fetchall()

    def find_genre_id(self, title):
        cur = self.con.cursor()
        row = cur.execute("SELECT id FROM genres WHERE title = ?",
                          (title,)).fetchone()
        if row:
            return row["id"]
        return None

    def add_genre(self, title):
        """Добавляет жанр, если такого ещё нет, и возвращает его id."""
        title = title.strip()
        if not title:
            return None
        if self.find_genre_id(title) is None:
            cur = self.con.cursor()
            cur.execute("INSERT INTO genres(title) VALUES(?)", (title,))
            self.con.commit()
        return self.find_genre_id(title)

    def rename_genre(self, genre_id, title):
        cur = self.con.cursor()
        cur.execute("UPDATE genres SET title = ? WHERE id = ?",
                    (title, genre_id))
        self.con.commit()

    def delete_genre(self, genre_id):
        """Удаляет жанр. У его книг жанр станет «не указан»."""
        cur = self.con.cursor()
        cur.execute("UPDATE books SET genre_id = NULL WHERE genre_id = ?",
                    (genre_id,))
        cur.execute("DELETE FROM genres WHERE id = ?", (genre_id,))
        self.con.commit()

    # ------------------------------------------------------------- книги
    def get_books(self, text="", genre="", status="", only_favorite=False,
                  order="books.title"):
        """Книги с учётом фильтров.

        Условия собираются в список и склеиваются через AND,
        а значения передаются через знаки ? (защита от SQL-инъекций).
        """
        conditions = []
        params = []
        if text:
            conditions.append("(books.title LIKE ? OR authors.name LIKE ?)")
            params.append(f"%{text}%")
            params.append(f"%{text}%")
        if genre:
            conditions.append("genres.title = ?")
            params.append(genre)
        if status:
            conditions.append("books.status = ?")
            params.append(status)
        if only_favorite:
            conditions.append("books.favorite = 1")

        query = BOOKS_QUERY
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY " + order

        cur = self.con.cursor()
        return cur.execute(query, params).fetchall()

    def get_book(self, book_id):
        cur = self.con.cursor()
        return cur.execute(BOOKS_QUERY + " WHERE books.id = ?",
                           (book_id,)).fetchone()

    def add_book(self, values):
        """Добавляет книгу. values: кортеж из 11 значений по порядку полей."""
        cur = self.con.cursor()
        cur.execute("""
            INSERT INTO books(title, author_id, genre_id, year, pages,
                              rating, status, favorite, cover, notes, added)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, values)
        self.con.commit()

    def update_book(self, book_id, values):
        """Изменяет книгу. values: те же 11 значений, что в add_book."""
        cur = self.con.cursor()
        cur.execute("""
            UPDATE books
            SET title = ?, author_id = ?, genre_id = ?, year = ?, pages = ?,
                rating = ?, status = ?, favorite = ?, cover = ?, notes = ?,
                added = ?
            WHERE id = ?
        """, values + (book_id,))
        self.con.commit()

    def set_status(self, book_id, status):
        cur = self.con.cursor()
        cur.execute("UPDATE books SET status = ? WHERE id = ?",
                    (status, book_id))
        self.con.commit()

    def delete_book(self, book_id):
        """Удаляет книгу вместе с её журналом чтения."""
        cur = self.con.cursor()
        cur.execute("DELETE FROM readings WHERE book_id = ?", (book_id,))
        cur.execute("DELETE FROM books WHERE id = ?", (book_id,))
        self.con.commit()

    # ----------------------------------------------------- журнал чтения
    def get_readings(self, book_id):
        cur = self.con.cursor()
        return cur.execute("""
            SELECT id, date, pages FROM readings
            WHERE book_id = ?
            ORDER BY date DESC
        """, (book_id,)).fetchall()

    def add_reading(self, book_id, date, pages):
        cur = self.con.cursor()
        cur.execute("INSERT INTO readings(book_id, date, pages) "
                    "VALUES(?, ?, ?)", (book_id, date, pages))
        self.con.commit()

    def delete_readings(self, ids):
        """Удаляет записи журнала с нужными id (как в уроке QT 7)."""
        cur = self.con.cursor()
        cur.execute("DELETE FROM readings WHERE id IN ("
                    + ", ".join("?" * len(ids)) + ")", ids)
        self.con.commit()

    # -------------------------------------------------------- статистика
    def count_by_status(self):
        """Словарь «статус: число книг» (агрегатная функция COUNT)."""
        result = {}
        for status in STATUSES:
            result[status] = 0
        cur = self.con.cursor()
        rows = cur.execute("SELECT status, COUNT(*) FROM books "
                           "GROUP BY status").fetchall()
        for row in rows:
            result[row[0]] = row[1]
        return result

    def pages_in_year(self, year):
        """Сколько страниц прочитано за год (агрегатная функция SUM)."""
        cur = self.con.cursor()
        row = cur.execute("SELECT SUM(pages) FROM readings "
                          "WHERE date LIKE ?", (f"{year}-%",)).fetchone()
        # Если записей нет, SUM вернёт None, поэтому подставляем 0
        return row[0] or 0

    def books_by_genre(self):
        """Список пар (жанр, число книг) для диаграммы."""
        cur = self.con.cursor()
        rows = cur.execute("""
            SELECT genres.title, COUNT(books.id)
            FROM books
            LEFT JOIN genres ON genres.id = books.genre_id
            GROUP BY books.genre_id
            ORDER BY COUNT(books.id) DESC
        """).fetchall()
        result = []
        for row in rows:
            result.append((row[0] or "Без жанра", row[1]))
        return result

    # --------------------------------------------------------- настройки
    def get_setting(self, name, default=""):
        cur = self.con.cursor()
        row = cur.execute("SELECT value FROM settings WHERE name = ?",
                          (name,)).fetchone()
        if row:
            return row[0]
        return default

    def set_setting(self, name, value):
        """Сохраняет настройку: изменяет, если она есть, иначе добавляет."""
        cur = self.con.cursor()
        row = cur.execute("SELECT value FROM settings WHERE name = ?",
                          (name,)).fetchone()
        if row:
            cur.execute("UPDATE settings SET value = ? WHERE name = ?",
                        (str(value), name))
        else:
            cur.execute("INSERT INTO settings(name, value) VALUES(?, ?)",
                        (name, str(value)))
        self.con.commit()

    # --------------------------------------------------------------- CSV
    def import_csv(self, path, added):
        """Добавляет книги из CSV-файла. Возвращает число добавленных книг."""
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))

        count = 0
        # Первая строка файла: заголовки, её пропускаем
        for row in rows[1:]:
            if len(row) < len(CSV_HEADER) or not row[0].strip():
                continue
            # Раскладываем строку файла по переменным
            title, author, genre, year, pages = row[0:5]
            rating, status, favorite, notes = row[5:9]
            if status not in STATUSES:
                status = STATUSES[0]
            values = (title.strip(), self.add_author(author),
                      self.add_genre(genre), to_int(year), to_int(pages),
                      min(to_int(rating), 5), status,
                      1 if to_int(favorite) else 0, "", notes, added)
            self.add_book(values)
            count += 1
        return count

    def export_csv(self, path, books):
        """Записывает книги в CSV-файл. Возвращает число записанных книг."""
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADER)
            for book in books:
                writer.writerow([book["title"], book["author"] or "",
                                 book["genre"] or "", book["year"],
                                 book["pages"], book["rating"],
                                 book["status"], book["favorite"],
                                 book["notes"]])
        return len(books)
