import sqlite3
import hashlib
import datetime
import os
import shutil

class FinanceManager:
    def __init__(self, db_name="finance.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        """Creates necessary tables if they do not exist."""
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )""")
        
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            category TEXT,
            type TEXT CHECK(type IN ('income', 'expense')),
            date TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )""")
        
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT,
            limit_amount REAL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )""")
        self.conn.commit()

    def register_user(self, username, password):
        """Registers a new user with a hashed password."""
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        try:
            self.cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            self.conn.commit()
            print("User registered successfully!")
        except sqlite3.IntegrityError:
            print("Username already exists!")

    def login_user(self, username, password):
        """Authenticates a user by verifying their credentials."""
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        self.cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, hashed_password))
        user = self.cursor.fetchone()
        if user:
            print("Login successful!")
            return user[0]
        else:
            print("Invalid credentials!")
            return None

    def add_transaction(self, user_id, amount, category, type, date):
        """Adds a transaction (income or expense) for a user."""
        self.cursor.execute("INSERT INTO transactions (user_id, amount, category, type, date) VALUES (?, ?, ?, ?, ?)",
                            (user_id, amount, category, type, date))
        self.conn.commit()
        print("Transaction added successfully!")

    def update_transaction(self, transaction_id, amount, category, type, date):
        """Updates an existing transaction."""
        self.cursor.execute("""
        UPDATE transactions SET amount = ?, category = ?, type = ?, date = ? WHERE id = ?""",
        (amount, category, type, date, transaction_id))
        self.conn.commit()
        print("Transaction updated successfully!")

    def delete_transaction(self, transaction_id):
        """Deletes a transaction by its ID."""
        self.cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        self.conn.commit()
        print("Transaction deleted successfully!")

    def get_financial_report(self, user_id, year, month):
        """Generates financial reports for a given month and year."""
        self.cursor.execute("""
        SELECT type, SUM(amount) FROM transactions WHERE user_id = ? AND date LIKE ? GROUP BY type""",
        (user_id, f"{year}-{month:02d}%"))
        report = self.cursor.fetchall()
        total_income = sum(amount for trans_type, amount in report if trans_type == 'income')
        total_expense = sum(amount for trans_type, amount in report if trans_type == 'expense')
        print(f"Total Income: {total_income}, Total Expenses: {total_expense}, Savings: {total_income - total_expense}")

    def set_budget(self, user_id, category, limit_amount):
        """Sets a budget limit for a specific category."""
        self.cursor.execute("INSERT INTO budgets (user_id, category, limit_amount) VALUES (?, ?, ?)",
                            (user_id, category, limit_amount))
        self.conn.commit()
        print("Budget set successfully!")

    def check_budget(self, user_id, category):
        """Checks if the user has exceeded their budget for a category."""
        self.cursor.execute("SELECT limit_amount FROM budgets WHERE user_id = ? AND category = ?", (user_id, category))
        budget = self.cursor.fetchone()
        if budget:
            self.cursor.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND category = ? AND type = 'expense'", (user_id, category))
            spent = self.cursor.fetchone()[0] or 0
            if spent > budget[0]:
                print(f"Warning: You have exceeded your budget limit for {category}!")
            else:
                print(f"Remaining budget for {category}: {budget[0] - spent}")
        else:
            print("No budget set for this category.")

    def backup_data(self, backup_dir="backup"):
        """Creates a backup of the database."""
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        shutil.copy("finance.db", os.path.join(backup_dir, "finance_backup.db"))
        print("Backup created successfully!")

    def restore_data(self, backup_path):
        """Restores the database from a backup file."""
        if os.path.exists(backup_path):
            shutil.copy(backup_path, "finance.db")
            print("Database restored successfully!")
        else:
            print("Backup file not found!")

# Example Usage:
if __name__ == "__main__":
    fm = FinanceManager()
    
    # Register and login
    fm.register_user("sanket", "password123")
    user_id = fm.login_user("sanket", "password123")
    
    if user_id:
        # Add, update, and delete transactions
        fm.add_transaction(user_id, 5000, "Salary", "income", "2025-02-04")
        fm.add_transaction(user_id, 200, "Food", "expense", "2025-02-04")
        fm.update_transaction(2, 250, "Food", "expense", "2025-02-04")
        fm.delete_transaction(2)
        
        # Get report
        fm.get_financial_report(user_id, 2025, 2)
        
        # Set and check budget
        fm.set_budget(user_id, "Food", 1000)
        fm.check_budget(user_id, "Food")
        
        # Backup and restore
        fm.backup_data()
        fm.restore_data("backup/finance_backup.db")
