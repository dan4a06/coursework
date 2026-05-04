"""
main_qt.py — Десктопный интерфейс библиотеки на PyQt5.
Вкладки: Жанры | Книги | Читатели | Выдачи | Возвраты | Отчёты
"""

import sys
from datetime import date, timedelta
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton,
    QDialog, QFormLayout, QLineEdit, QDoubleSpinBox, QSpinBox,
    QComboBox, QDateEdit, QLabel, QMessageBox, QHeaderView,
    QGroupBox, QTextEdit
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont

from database import Database


# ──────────────────────────── helpers ────────────────────────────

def make_table(headers: list[str]) -> QTableWidget:
    tw = QTableWidget()
    tw.setColumnCount(len(headers))
    tw.setHorizontalHeaderLabels(headers)
    tw.setEditTriggers(QTableWidget.NoEditTriggers)
    tw.setSelectionBehavior(QTableWidget.SelectRows)
    tw.setAlternatingRowColors(True)
    tw.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    tw.verticalHeader().setVisible(False)
    return tw


def set_item(table: QTableWidget, row: int, col: int, text: str):
    item = QTableWidgetItem(str(text) if text is not None else '')
    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
    table.setItem(row, col, item)


# ──────────────────────── Диалог: Жанр ───────────────────────────

class GenreDialog(QDialog):
    def __init__(self, parent=None, name: str = ''):
        super().__init__(parent)
        self.setWindowTitle('Жанр')
        layout = QFormLayout(self)
        self.name_edit = QLineEdit(name)
        layout.addRow('Название:', self.name_edit)
        btns = QHBoxLayout()
        ok = QPushButton('OK')
        cancel = QPushButton('Отмена')
        btns.addWidget(ok)
        btns.addWidget(cancel)
        layout.addRow(btns)
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)

    def get_data(self):
        return self.name_edit.text().strip()


# ──────────────────────── Диалог: Книга ──────────────────────────

class BookDialog(QDialog):
    def __init__(self, db: Database, parent=None, data: dict = None):
        super().__init__(parent)
        self.setWindowTitle('Книга')
        self.db = db
        layout = QFormLayout(self)

        self.title_edit = QLineEdit()
        self.author_edit = QLineEdit()
        self.genre_combo = QComboBox()
        self.deposit_spin = QDoubleSpinBox()
        self.deposit_spin.setRange(0, 100000)
        self.deposit_spin.setSuffix(' ₽')
        self.rental_spin = QDoubleSpinBox()
        self.rental_spin.setRange(0, 100000)
        self.rental_spin.setSuffix(' ₽')
        self.copies_spin = QSpinBox()
        self.copies_spin.setRange(1, 100)

        self._genres = db.get_genres()
        for g in self._genres:
            self.genre_combo.addItem(g['name'], g['id'])

        layout.addRow('Название:', self.title_edit)
        layout.addRow('Автор:', self.author_edit)
        layout.addRow('Жанр:', self.genre_combo)
        layout.addRow('Залог:', self.deposit_spin)
        layout.addRow('Стоимость проката:', self.rental_spin)
        layout.addRow('Экземпляров:', self.copies_spin)

        if data:
            self.title_edit.setText(data.get('title', ''))
            self.author_edit.setText(data.get('author', ''))
            self.deposit_spin.setValue(data.get('deposit', 0))
            self.rental_spin.setValue(data.get('rental_price', 0))
            self.copies_spin.setValue(data.get('total_copies', 1))
            for i, g in enumerate(self._genres):
                if g['id'] == data.get('genre_id'):
                    self.genre_combo.setCurrentIndex(i)
                    break

        btns = QHBoxLayout()
        ok = QPushButton('OK')
        cancel = QPushButton('Отмена')
        btns.addWidget(ok)
        btns.addWidget(cancel)
        layout.addRow(btns)
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)

    def get_data(self):
        return {
            'title': self.title_edit.text().strip(),
            'author': self.author_edit.text().strip(),
            'genre_id': self.genre_combo.currentData(),
            'deposit': self.deposit_spin.value(),
            'rental_price': self.rental_spin.value(),
            'total_copies': self.copies_spin.value(),
        }


# ──────────────────────── Диалог: Читатель ───────────────────────

class ReaderDialog(QDialog):
    def __init__(self, parent=None, data: dict = None):
        super().__init__(parent)
        self.setWindowTitle('Читатель')
        layout = QFormLayout(self)

        self.surname_edit = QLineEdit()
        self.name_edit = QLineEdit()
        self.patronymic_edit = QLineEdit()
        self.address_edit = QLineEdit()
        self.phone_edit = QLineEdit()

        layout.addRow('Фамилия:', self.surname_edit)
        layout.addRow('Имя:', self.name_edit)
        layout.addRow('Отчество:', self.patronymic_edit)
        layout.addRow('Адрес:', self.address_edit)
        layout.addRow('Телефон:', self.phone_edit)

        if data:
            self.surname_edit.setText(data.get('surname', ''))
            self.name_edit.setText(data.get('name', ''))
            self.patronymic_edit.setText(data.get('patronymic', ''))
            self.address_edit.setText(data.get('address', ''))
            self.phone_edit.setText(data.get('phone', ''))

        btns = QHBoxLayout()
        ok = QPushButton('OK')
        cancel = QPushButton('Отмена')
        btns.addWidget(ok)
        btns.addWidget(cancel)
        layout.addRow(btns)
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)

    def get_data(self):
        return {
            'surname': self.surname_edit.text().strip(),
            'name': self.name_edit.text().strip(),
            'patronymic': self.patronymic_edit.text().strip(),
            'address': self.address_edit.text().strip(),
            'phone': self.phone_edit.text().strip(),
        }


# ──────────────────────── Диалог: Выдача ─────────────────────────

class RentalDialog(QDialog):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle('Выдать книгу')
        layout = QFormLayout(self)

        self.book_combo = QComboBox()
        self.reader_combo = QComboBox()
        self.issue_date = QDateEdit(QDate.currentDate())
        self.issue_date.setCalendarPopup(True)
        self.issue_date.setDisplayFormat('yyyy-MM-dd')
        self.return_date = QDateEdit(QDate.currentDate().addDays(14))
        self.return_date.setCalendarPopup(True)
        self.return_date.setDisplayFormat('yyyy-MM-dd')

        self._books = [b for b in db.get_books() if db.available_copies(b['id']) > 0]
        for b in self._books:
            avail = db.available_copies(b['id'])
            self.book_combo.addItem(f"{b['title']} ({avail} дост.)", b['id'])

        self._readers = db.get_readers()
        for r in self._readers:
            self.reader_combo.addItem(f"{r['surname']} {r['name']} {r['patronymic']}", r['id'])

        layout.addRow('Книга:', self.book_combo)
        layout.addRow('Читатель:', self.reader_combo)
        layout.addRow('Дата выдачи:', self.issue_date)
        layout.addRow('Ожидаемый возврат:', self.return_date)

        btns = QHBoxLayout()
        ok = QPushButton('Выдать')
        cancel = QPushButton('Отмена')
        btns.addWidget(ok)
        btns.addWidget(cancel)
        layout.addRow(btns)
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)

    def get_data(self):
        return {
            'book_id': self.book_combo.currentData(),
            'reader_id': self.reader_combo.currentData(),
            'issue_date': self.issue_date.date().toString('yyyy-MM-dd'),
            'expected_return': self.return_date.date().toString('yyyy-MM-dd'),
        }


# ──────────────────────── Вкладка: Жанры ─────────────────────────

class GenresTab(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        layout = QVBoxLayout(self)

        self.table = make_table(['ID', 'Название'])
        layout.addWidget(self.table)

        btns = QHBoxLayout()
        self.btn_add = QPushButton('Добавить')
        self.btn_edit = QPushButton('Изменить')
        self.btn_del = QPushButton('Удалить')
        for b in [self.btn_add, self.btn_edit, self.btn_del]:
            btns.addWidget(b)
        btns.addStretch()
        layout.addLayout(btns)

        self.btn_add.clicked.connect(self.add)
        self.btn_edit.clicked.connect(self.edit)
        self.btn_del.clicked.connect(self.delete)
        self.refresh()

    def refresh(self):
        rows = self.db.get_genres()
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            set_item(self.table, i, 0, r['id'])
            set_item(self.table, i, 1, r['name'])

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return int(self.table.item(row, 0).text())

    def add(self):
        dlg = GenreDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            name = dlg.get_data()
            if name:
                self.db.add_genre(name)
                self.refresh()

    def edit(self):
        gid = self._selected_id()
        if gid is None:
            QMessageBox.warning(self, 'Внимание', 'Выберите жанр')
            return
        row = self.table.currentRow()
        old_name = self.table.item(row, 1).text()
        dlg = GenreDialog(self, name=old_name)
        if dlg.exec_() == QDialog.Accepted:
            name = dlg.get_data()
            if name:
                self.db.update_genre(gid, name)
                self.refresh()

    def delete(self):
        gid = self._selected_id()
        if gid is None:
            QMessageBox.warning(self, 'Внимание', 'Выберите жанр')
            return
        if QMessageBox.question(self, 'Удалить?', 'Удалить жанр?') == QMessageBox.Yes:
            self.db.delete_genre(gid)
            self.refresh()


# ──────────────────────── Вкладка: Книги ─────────────────────────

class BooksTab(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        layout = QVBoxLayout(self)

        headers = ['ID', 'Название', 'Автор', 'Жанр', 'Залог (₽)', 'Прокат (₽)', 'Экз.', 'Доступно']
        self.table = make_table(headers)
        layout.addWidget(self.table)

        btns = QHBoxLayout()
        self.btn_add = QPushButton('Добавить')
        self.btn_edit = QPushButton('Изменить')
        self.btn_del = QPushButton('Удалить')
        for b in [self.btn_add, self.btn_edit, self.btn_del]:
            btns.addWidget(b)
        btns.addStretch()
        layout.addLayout(btns)

        self.btn_add.clicked.connect(self.add)
        self.btn_edit.clicked.connect(self.edit)
        self.btn_del.clicked.connect(self.delete)
        self.refresh()

    def refresh(self):
        rows = self.db.get_books()
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            avail = self.db.available_copies(r['id'])
            set_item(self.table, i, 0, r['id'])
            set_item(self.table, i, 1, r['title'])
            set_item(self.table, i, 2, r['author'])
            set_item(self.table, i, 3, r['genre_name'] or '—')
            set_item(self.table, i, 4, f"{r['deposit']:.2f}")
            set_item(self.table, i, 5, f"{r['rental_price']:.2f}")
            set_item(self.table, i, 6, r['total_copies'])
            set_item(self.table, i, 7, avail)

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return int(self.table.item(row, 0).text())

    def add(self):
        dlg = BookDialog(self.db, self)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.get_data()
            if d['title'] and d['author']:
                self.db.add_book(**d)
                self.refresh()

    def edit(self):
        bid = self._selected_id()
        if bid is None:
            QMessageBox.warning(self, 'Внимание', 'Выберите книгу')
            return
        row_data = self.db.get_book(bid)
        dlg = BookDialog(self.db, self, dict(row_data))
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.get_data()
            self.db.update_book(bid, **d)
            self.refresh()

    def delete(self):
        bid = self._selected_id()
        if bid is None:
            QMessageBox.warning(self, 'Внимание', 'Выберите книгу')
            return
        if QMessageBox.question(self, 'Удалить?', 'Удалить книгу?') == QMessageBox.Yes:
            self.db.delete_book(bid)
            self.refresh()


# ──────────────────────── Вкладка: Читатели ──────────────────────

class ReadersTab(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        layout = QVBoxLayout(self)

        headers = ['ID', 'Фамилия', 'Имя', 'Отчество', 'Адрес', 'Телефон']
        self.table = make_table(headers)
        layout.addWidget(self.table)

        btns = QHBoxLayout()
        self.btn_add = QPushButton('Добавить')
        self.btn_edit = QPushButton('Изменить')
        self.btn_del = QPushButton('Удалить')
        for b in [self.btn_add, self.btn_edit, self.btn_del]:
            btns.addWidget(b)
        btns.addStretch()
        layout.addLayout(btns)

        self.btn_add.clicked.connect(self.add)
        self.btn_edit.clicked.connect(self.edit)
        self.btn_del.clicked.connect(self.delete)
        self.refresh()

    def refresh(self):
        rows = self.db.get_readers()
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            set_item(self.table, i, 0, r['id'])
            set_item(self.table, i, 1, r['surname'])
            set_item(self.table, i, 2, r['name'])
            set_item(self.table, i, 3, r['patronymic'])
            set_item(self.table, i, 4, r['address'])
            set_item(self.table, i, 5, r['phone'])

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return int(self.table.item(row, 0).text())

    def add(self):
        dlg = ReaderDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.get_data()
            if d['surname'] and d['name']:
                self.db.add_reader(**d)
                self.refresh()

    def edit(self):
        rid = self._selected_id()
        if rid is None:
            QMessageBox.warning(self, 'Внимание', 'Выберите читателя')
            return
        row_data = self.db.get_reader(rid)
        dlg = ReaderDialog(self, dict(row_data))
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.get_data()
            self.db.update_reader(rid, **d)
            self.refresh()

    def delete(self):
        rid = self._selected_id()
        if rid is None:
            QMessageBox.warning(self, 'Внимание', 'Выберите читателя')
            return
        if QMessageBox.question(self, 'Удалить?', 'Удалить читателя?') == QMessageBox.Yes:
            self.db.delete_reader(rid)
            self.refresh()


# ──────────────────────── Вкладка: Выдачи ────────────────────────

class RentalsTab(QWidget):
    def __init__(self, db: Database, returns_tab=None):
        super().__init__()
        self.db = db
        self._returns_tab = returns_tab
        layout = QVBoxLayout(self)

        headers = ['ID', 'Книга', 'Читатель', 'Дата выдачи', 'Ожид. возврат', 'Статус', 'Залог (₽)']
        self.table = make_table(headers)
        layout.addWidget(self.table)

        btns = QHBoxLayout()
        self.btn_add = QPushButton('Выдать книгу')
        self.btn_return = QPushButton('Оформить возврат')
        self.btn_del = QPushButton('Удалить запись')
        for b in [self.btn_add, self.btn_return, self.btn_del]:
            btns.addWidget(b)
        btns.addStretch()
        layout.addLayout(btns)

        self.btn_add.clicked.connect(self.add)
        self.btn_return.clicked.connect(self.process_return)
        self.btn_del.clicked.connect(self.delete)
        self.refresh()

    def set_returns_tab(self, tab):
        self._returns_tab = tab

    def refresh(self):
        rows = self.db.get_rentals()
        self.table.setRowCount(len(rows))
        today = date.today().isoformat()
        for i, r in enumerate(rows):
            set_item(self.table, i, 0, r['id'])
            set_item(self.table, i, 1, r['title'])
            set_item(self.table, i, 2, r['reader_name'])
            set_item(self.table, i, 3, r['issue_date'])
            set_item(self.table, i, 4, r['expected_return'])
            if r['returned']:
                status = 'Возвращена'
            elif r['expected_return'] < today:
                status = '⚠ Просрочена'
            else:
                status = 'На руках'
            set_item(self.table, i, 5, status)
            set_item(self.table, i, 6, f"{r['deposit']:.2f}")

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return int(self.table.item(row, 0).text())

    def add(self):
        dlg = RentalDialog(self.db, self)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.get_data()
            self.db.add_rental(**d)
            self.refresh()

    def process_return(self):
        rid = self._selected_id()
        if rid is None:
            QMessageBox.warning(self, 'Внимание', 'Выберите запись о выдаче')
            return
        rental = self.db.get_rental(rid)
        if rental and rental['returned']:
            QMessageBox.information(self, 'Уже возвращена', 'Эта книга уже была возвращена.')
            return
        if rental:
            msg = (f"Книга: {rental['title']}\n"
                   f"Читатель: {rental['reader_name']}\n"
                   f"Стоимость проката: {rental['rental_price']:.2f} ₽\n\n"
                   "Оформить возврат сегодняшней датой?")
            if QMessageBox.question(self, 'Подтверждение', msg) == QMessageBox.Yes:
                today = date.today().isoformat()
                amount = self.db.process_return(rid, today)
                QMessageBox.information(self, 'Возврат оформлен',
                                        f'Читатель получает залог обратно.\nПлата за прокат: {amount:.2f} ₽')
                self.refresh()
                if self._returns_tab:
                    self._returns_tab.refresh()

    def delete(self):
        rid = self._selected_id()
        if rid is None:
            QMessageBox.warning(self, 'Внимание', 'Выберите запись')
            return
        if QMessageBox.question(self, 'Удалить?', 'Удалить запись о выдаче?') == QMessageBox.Yes:
            self.db.delete_rental(rid)
            self.refresh()


# ──────────────────────── Вкладка: Возвраты ──────────────────────

class ReturnsTab(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        layout = QVBoxLayout(self)

        label = QLabel('История возвратов и оплат')
        label.setFont(QFont('Arial', 10, QFont.Bold))
        layout.addWidget(label)

        headers = ['ID', 'Книга', 'Читатель', 'Дата выдачи', 'Дата возврата', 'Оплачено (₽)']
        self.table = make_table(headers)
        layout.addWidget(self.table)

        # Итог
        self.total_label = QLabel()
        layout.addWidget(self.total_label)

        btn_refresh = QPushButton('Обновить')
        btn_refresh.clicked.connect(self.refresh)
        layout.addWidget(btn_refresh)
        self.refresh()

    def refresh(self):
        rows = self.db.get_returns()
        self.table.setRowCount(len(rows))
        total = 0.0
        for i, r in enumerate(rows):
            set_item(self.table, i, 0, r['id'])
            set_item(self.table, i, 1, r['title'])
            set_item(self.table, i, 2, r['reader_name'])
            set_item(self.table, i, 3, r['issue_date'])
            set_item(self.table, i, 4, r['return_date'])
            set_item(self.table, i, 5, f"{r['amount_paid']:.2f}")
            total += r['amount_paid']
        self.total_label.setText(f'Итого выручка: {total:.2f} ₽')


# ──────────────────────── Вкладка: Отчёты ────────────────────────

class ReportsTab(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        layout = QVBoxLayout(self)

        # Активные выдачи
        grp1 = QGroupBox('Текущие выдачи (книги на руках)')
        g1_layout = QVBoxLayout(grp1)
        headers1 = ['ID', 'Книга', 'Читатель', 'Дата выдачи', 'Ожид. возврат', 'Залог (₽)']
        self.active_table = make_table(headers1)
        g1_layout.addWidget(self.active_table)
        layout.addWidget(grp1)

        # Выручка по книгам
        grp2 = QGroupBox('Выручка по книгам')
        g2_layout = QVBoxLayout(grp2)
        headers2 = ['Книга', 'Кол-во выдач', 'Итого (₽)']
        self.revenue_table = make_table(headers2)
        g2_layout.addWidget(self.revenue_table)
        layout.addWidget(grp2)

        btn = QPushButton('Обновить отчёты')
        btn.clicked.connect(self.refresh)
        layout.addWidget(btn)
        self.refresh()

    def refresh(self):
        active = self.db.report_active_rentals()
        self.active_table.setRowCount(len(active))
        for i, r in enumerate(active):
            set_item(self.active_table, i, 0, r['id'])
            set_item(self.active_table, i, 1, r['title'])
            set_item(self.active_table, i, 2, r['reader'])
            set_item(self.active_table, i, 3, r['issue_date'])
            set_item(self.active_table, i, 4, r['expected_return'])
            set_item(self.active_table, i, 5, f"{r['deposit']:.2f}")

        revenue = self.db.report_revenue()
        self.revenue_table.setRowCount(len(revenue))
        for i, r in enumerate(revenue):
            set_item(self.revenue_table, i, 0, r['title'])
            set_item(self.revenue_table, i, 1, r['times_rented'])
            set_item(self.revenue_table, i, 2, f"{r['total_income']:.2f}")


# ──────────────────────── Главное окно ───────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Библиотека — система проката книг')
        self.setMinimumSize(1000, 650)

        self.db = Database('library.db')
        tabs = QTabWidget()

        self.genres_tab  = GenresTab(self.db)
        self.books_tab   = BooksTab(self.db)
        self.readers_tab = ReadersTab(self.db)
        self.returns_tab = ReturnsTab(self.db)
        self.rentals_tab = RentalsTab(self.db, self.returns_tab)
        self.reports_tab = ReportsTab(self.db)

        tabs.addTab(self.genres_tab,  '📚 Жанры')
        tabs.addTab(self.books_tab,   '📖 Книги')
        tabs.addTab(self.readers_tab, '👤 Читатели')
        tabs.addTab(self.rentals_tab, '📤 Выдачи')
        tabs.addTab(self.returns_tab, '📥 Возвраты')
        tabs.addTab(self.reports_tab, '📊 Отчёты')

        # При переключении вкладок обновляем данные
        tabs.currentChanged.connect(self._on_tab_changed)

        self.setCentralWidget(tabs)
        self.tabs = tabs

    def _on_tab_changed(self, idx):
        widget = self.tabs.widget(idx)
        if hasattr(widget, 'refresh'):
            widget.refresh()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()