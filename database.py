import sqlite3
import os
from config import DATABASE_NAME

class Database:
    def __init__(self):
        self.db_name = DATABASE_NAME
        self.init_database()
    
    def get_connection(self):
        return sqlite3.connect(self.db_name)
    
    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                language TEXT DEFAULT 'RU',
                username TEXT
            )
        ''')
        
        # Таблица кошельков
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS wallets (
                wallet_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                display_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Таблица сделок
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deals (
                deal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                creator_id INTEGER,
                buyer_id INTEGER,
                deal_type TEXT,
                description TEXT,
                price_usdt REAL,
                invoice_id TEXT,
                invoice_url TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (creator_id) REFERENCES users(user_id),
                FOREIGN KEY (buyer_id) REFERENCES users(user_id)
            )
        ''')
        
        # Таблица балансов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS balances (
                user_id INTEGER PRIMARY KEY,
                balance REAL DEFAULT 0.0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Таблица админов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_user(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return user
    
    def create_user(self, user_id, username=None, language='RU'):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, username, language)
            VALUES (?, ?, ?)
        ''', (user_id, username, language))
        conn.commit()
        conn.close()
    
    def update_user_language(self, user_id, language):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users SET language = ? WHERE user_id = ?
        ''', (language, user_id))
        conn.commit()
        conn.close()
    
    def get_user_language(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        if result and result[0]:
            return result[0]
        return None
    
    def add_wallet(self, user_id, display_name):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO wallets (user_id, display_name)
            VALUES (?, ?)
        ''', (user_id, display_name))
        wallet_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return wallet_id
    
    def get_user_wallets(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT wallet_id, display_name, created_at
            FROM wallets
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))
        wallets = cursor.fetchall()
        conn.close()
        return wallets
    
    def create_deal(self, creator_id, deal_type, description, price_usdt, invoice_id=None, invoice_url=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO deals (creator_id, deal_type, description, price_usdt, invoice_id, invoice_url)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (creator_id, deal_type, description, price_usdt, invoice_id, invoice_url))
        deal_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return deal_id
    
    def get_deal(self, deal_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM deals WHERE deal_id = ?', (deal_id,))
        deal = cursor.fetchone()
        conn.close()
        return deal
    
    def update_deal_invoice(self, deal_id, invoice_id, invoice_url):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE deals SET invoice_id = ?, invoice_url = ?
            WHERE deal_id = ?
        ''', (invoice_id, invoice_url, deal_id))
        conn.commit()
        conn.close()
    
    def update_deal_status(self, deal_id, status, buyer_id=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        if buyer_id:
            cursor.execute('''
                UPDATE deals SET status = ?, buyer_id = ?
                WHERE deal_id = ?
            ''', (status, buyer_id, deal_id))
        else:
            cursor.execute('''
                UPDATE deals SET status = ?
                WHERE deal_id = ?
            ''', (status, deal_id))
        conn.commit()
        conn.close()
    
    # Методы для работы с балансами
    def get_balance(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT balance FROM balances WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return result[0]
        # Создаем запись с нулевым балансом если её нет
        self.set_balance(user_id, 0.0)
        return 0.0
    
    def set_balance(self, user_id, balance):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO balances (user_id, balance, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, balance))
        conn.commit()
        conn.close()
    
    def add_balance(self, user_id, amount):
        current_balance = self.get_balance(user_id)
        new_balance = current_balance + amount
        self.set_balance(user_id, new_balance)
        return new_balance
    
    def subtract_balance(self, user_id, amount):
        current_balance = self.get_balance(user_id)
        if current_balance >= amount:
            new_balance = current_balance - amount
            self.set_balance(user_id, new_balance)
            return new_balance
        return None  # Недостаточно средств
    
    # Методы для работы с админами
    def is_admin(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM admins WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    def add_admin(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO admins (user_id)
            VALUES (?)
        ''', (user_id,))
        conn.commit()
        conn.close()
    
    def remove_admin(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM admins WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
    
    def get_all_users(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, username FROM users')
        users = cursor.fetchall()
        conn.close()
        return users

