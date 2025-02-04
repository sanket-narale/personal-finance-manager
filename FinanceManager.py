import sqlite3
import hashlib
import shutil
import os

class FinanceManager:
    def __init__(self, db_name="finance.db"):
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        """)
        
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            category TEXT,
            type TEXT CHECK(type IN ('income', 'expense')),
            date TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)
        
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT,
            limit_amount REAL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)
        self.conn.commit()

    def register_user(self, username, password):
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        try:
            self.cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            self.conn.commit()
            print("User registered successfully!")
        except sqlite3.IntegrityError:
            print("Username already exists!")

    def login_user(self, username, password):
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        self.cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, hashed_password))
        user = self.cursor.fetchone()
        if user:
            print("Login successful!")
            return user[0]
        else:
            print("Invalid credentials!")
            return None

    def add_transaction(self, user_id, amount, category, transaction_type, date):
        if transaction_type not in ['income', 'expense']:
            print("Invalid transaction type. Use 'income' or 'expense'.")
            return
        self.cursor.execute("INSERT INTO transactions (user_id, amount, category, type, date) VALUES (?, ?, ?, ?, ?)",
                            (user_id, amount, category, transaction_type, date))
        self.conn.commit()
        print("Transaction added successfully!")

    def get_financial_report(self, user_id, period="monthly"):
        if not user_id:
            print("Login required to view financial reports!")
            return
        
        query = ""
        if period == "monthly":
            query = "SELECT type, SUM(amount) FROM transactions WHERE user_id = ? AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now') GROUP BY type"
        elif period == "yearly":
            query = "SELECT type, SUM(amount) FROM transactions WHERE user_id = ? AND strftime('%Y', date) = strftime('%Y', 'now') GROUP BY type"
        else:
            print("Invalid period. Use 'monthly' or 'yearly'.")
            return
        
        self.cursor.execute(query, (user_id,))
        report = self.cursor.fetchall()
        
        total_income = sum(amount for trans_type, amount in report if trans_type == 'income') or 0
        total_expense = sum(amount for trans_type, amount in report if trans_type == 'expense') or 0
        
        print(f"Total Income: {total_income}, Total Expenses: {total_expense}, Savings: {total_income - total_expense}")

    def check_budget(self, user_id, category):
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

    def backup_data(self, backup_path="backup.db"):
        shutil.copy(self.db_name, backup_path)
        print("Database backup created successfully!")

    def restore_data(self, backup_path="backup.db"):
        if os.path.exists(backup_path):
            shutil.copy(backup_path, self.db_name)
            print("Database restored successfully!")
        else:
            print("Backup file not found!")

# CLI Menu Implementation
def main():
    fm = FinanceManager()
    user_id = None

    while True:
        print("\nPersonal Finance Manager")
        print("1. Register")
        print("2. Login")
        print("3. Add Transaction")
        print("4. View Financial Report")
        print("5. Check Budget")
        print("6. Backup Data")
        print("7. Restore Data")
        print("8. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            username = input("Enter username: ")
            password = input("Enter password: ")
            fm.register_user(username, password)
        elif choice == "2":
            username = input("Enter username: ")
            password = input("Enter password: ")
            user_id = fm.login_user(username, password)
        elif choice == "3" and user_id:
            amount = float(input("Enter amount: "))
            category = input("Enter category: ")
            transaction_type = input("Enter type (income/expense): ")
            date = input("Enter date (YYYY-MM-DD): ")
            fm.add_transaction(user_id, amount, category, transaction_type, date)
        elif choice == "4" and user_id:
            period = input("Enter period (monthly/yearly): ")
            fm.get_financial_report(user_id, period)
        elif choice == "5" and user_id:
            category = input("Enter category: ")
            fm.check_budget(user_id, category)
        elif choice == "6":
            fm.backup_data()
        elif choice == "7":
            fm.restore_data()
        elif choice == "8":
            print("Exiting program. Goodbye!")
            break
        else:
            print("Invalid choice or login required!")

if __name__ == "__main__":
    main()
