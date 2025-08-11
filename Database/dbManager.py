# Database/dbManager.py
# Description: This file contains the UserDBManager class for managing the SQLite database.
import sqlite3
import logging
import json
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserDBManager:
    def __init__(self, db_name='hidyBot.db'):
        """Initialize the database manager and create tables if they don't exist."""
        self.db_name = db_name
        self.conn = self.create_connection()
        if self.conn:
            self.create_user_table()
            self.set_default_configs()

    def create_connection(self):
        """Create a database connection to the SQLite database."""
        try:
            conn = sqlite3.connect(self.db_name)
            # Enable foreign key constraints
            conn.execute("PRAGMA foreign_keys = ON")
            return conn
        except sqlite3.Error as e:
            logger.error(f"Error creating database connection: {e}")
            return None

    def create_user_table(self):
        """Create all necessary tables if they don't exist."""
        if not self.conn:
            logger.error("No database connection available.")
            return

        cur = self.conn.cursor()

        # Users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                phone_number TEXT,
                balance INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT,
                banned BOOLEAN DEFAULT 0,
                test_subscription BOOLEAN DEFAULT 1,
                comment TEXT
            )
        """)
        self.conn.commit()
        logger.info("Users table created successfully!")

        # Servers table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS servers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                user_limit INTEGER,
                status BOOLEAN DEFAULT 1,
                comment TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        self.conn.commit()
        logger.info("Servers table created successfully!")

        # Plans table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                size_gb REAL NOT NULL,
                days INTEGER NOT NULL,
                price INTEGER NOT NULL,
                server_id INTEGER NOT NULL,
                status BOOLEAN DEFAULT 1,
                description TEXT,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (server_id) REFERENCES servers (id)
            )
        """)
        self.conn.commit()
        logger.info("Plans table created successfully!")

        # Orders table (Updated structure)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                plan_id INTEGER NOT NULL,
                server_id INTEGER NOT NULL,
                uuid TEXT NOT NULL UNIQUE,
                price INTEGER NOT NULL,
                status BOOLEAN DEFAULT 1,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (telegram_id) REFERENCES users (telegram_id),
                FOREIGN KEY (plan_id) REFERENCES plans (id),
                FOREIGN KEY (server_id) REFERENCES servers (id)
            )
        """)
        self.conn.commit()
        logger.info("Orders table created successfully!")

        # Payments table (Updated structure)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                payment_amount INTEGER NOT NULL,
                approved BOOLEAN, -- NULL = pending, 0 = rejected, 1 = approved
                authority TEXT,
                payment_method TEXT, -- 'Card', 'Digital', 'Online'
                photo_path TEXT,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (telegram_id) REFERENCES users (telegram_id)
            )
        """)
        self.conn.commit()
        logger.info("Payments table created successfully!")

        # Non-order subscriptions table (For manually added subscriptions)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS non_order_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                uuid TEXT NOT NULL UNIQUE,
                server_id INTEGER NOT NULL,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (telegram_id) REFERENCES users (telegram_id),
                FOREIGN KEY (server_id) REFERENCES servers (id)
            )
        """)
        self.conn.commit()
        logger.info("Non-order subscriptions table created successfully!")

        # Test subscriptions table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS test_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                uuid TEXT NOT NULL UNIQUE,
                server_id INTEGER NOT NULL,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (telegram_id) REFERENCES users (telegram_id),
                FOREIGN KEY (server_id) REFERENCES servers (id)
            )
        """)
        self.conn.commit()
        logger.info("Test subscriptions table created successfully!")

        # Events table (For logging user activities)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                event_type TEXT NOT NULL,
                details TEXT,
                created_at TEXT,
                FOREIGN KEY (telegram_id) REFERENCES users (telegram_id)
            )
        """)
        self.conn.commit()
        logger.info("Events table created successfully!")

        # Integer config table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS int_config (
                key TEXT PRIMARY KEY,
                value INTEGER
            )
        """)
        self.conn.commit()
        logger.info("Int config table created successfully!")

        # String config table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS str_config (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        self.conn.commit()
        logger.info("String config table created successfully!")

        # Boolean config table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bool_config (
                key TEXT PRIMARY KEY,
                value BOOLEAN
            )
        """)
        self.conn.commit()
        logger.info("Boolean config table created successfully!")

        # New tables for enhanced features

        # Referrals table (For affiliate system)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER NOT NULL,
                referred_id INTEGER NOT NULL,
                commission INTEGER DEFAULT 0,
                created_at TEXT,
                FOREIGN KEY (referrer_id) REFERENCES users (telegram_id),
                FOREIGN KEY (referred_id) REFERENCES users (telegram_id),
                UNIQUE(referrer_id, referred_id)
            )
        """)
        self.conn.commit()
        logger.info("Referrals table created successfully!")

        # Coupons table (For discount coupons)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS coupons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                discount_type TEXT NOT NULL, -- 'percentage' or 'fixed'
                discount_value INTEGER NOT NULL, -- percentage (0-100) or fixed amount in Rials
                usage_limit INTEGER, -- NULL for unlimited
                used_count INTEGER DEFAULT 0,
                expiry_date TEXT, -- NULL for no expiry
                is_active BOOLEAN DEFAULT 1,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        self.conn.commit()
        logger.info("Coupons table created successfully!")

        # Coupon usage table (Track who used which coupon)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS coupon_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coupon_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                used_at TEXT,
                FOREIGN KEY (coupon_id) REFERENCES coupons (id),
                FOREIGN KEY (user_id) REFERENCES users (telegram_id)
            )
        """)
        self.conn.commit()
        logger.info("Coupon usage table created successfully!")

        # Online payment transactions table (For tracking online payments)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS online_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_id INTEGER NOT NULL, -- Reference to payments table
                gateway TEXT NOT NULL, -- 'ZarinPal', 'NextPay', etc.
                transaction_id TEXT, -- Gateway transaction ID
                callback_url TEXT,
                status TEXT, -- 'pending', 'completed', 'failed', 'cancelled'
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (payment_id) REFERENCES payments (id)
            )
        """)
        self.conn.commit()
        logger.info("Online payments table created successfully!")

    def set_default_configs(self):
        """Set default configuration values if they don't exist."""
        if not self.conn:
            logger.error("No database connection available.")
            return

        cur = self.conn.cursor()

        # Default integer configs
        int_configs = {
            'min_deposit_amount': 10000,  # 10,000 Tomans
            'test_sub_days': 1,
            'test_sub_size_gb': 1,
            'reminder_notification_days': 3,
            'reminder_notification_usage': 3,
            'advanced_renewal_days': 3,
            'advanced_renewal_usage': 3
        }

        for key, value in int_configs.items():
            cur.execute("INSERT OR IGNORE INTO int_config (key, value) VALUES (?, ?)", (key, value))

        # Default string configs
        str_configs = {
            'channel_id': '',
            'msg_user_start': 'به ربات خوش آمدید!',
            'msg_faq': 'سوالات متداول:\n1. چگونه اشتراک بخرم؟\n2. چگونه از کانفیگ استفاده کنم؟',
            'msg_help': 'راهنما:\nبرای استفاده از ربات، ابتدا باید اشتراک تهیه کنید.',
            'msg_force_join_channel': 'لطفاً ابتدا در کانال زیر عضو شوید:',
            'support_username': '',
            'card_number': '',
            'card_holder': ''
        }

        for key, value in str_configs.items():
            cur.execute("INSERT OR IGNORE INTO str_config (key, value) VALUES (?, ?)", (key, value))

        # Default boolean configs
        bool_configs = {
            'visible_hiddify_hyperlink': 1,
            'three_random_num_price': 0,
            'force_join_channel': 0,
            'buy_subscription_status': 1,
            'renewal_subscription_status': 1,
            'visible_conf_dir': 1,
            'visible_conf_sub_auto': 1,
            'visible_conf_sub_url': 1,
            'visible_conf_sub_qr': 1,
            'visible_conf_clash': 1,
            'visible_conf_hiddify': 1,
            'visible_conf_sub_sing_box': 1,
            'visible_conf_sub_full_sing_box': 1,
            'reminder_notification': 1,
            'test_subscription': 1,
            'panel_auto_backup': 1,
            'bot_auto_backup': 1
        }

        for key, value in bool_configs.items():
            cur.execute("INSERT OR IGNORE INTO bool_config (key, value) VALUES (?, ?)", (key, value))

        self.conn.commit()
        logger.info("Default configurations set successfully!")

    # --- User Management Methods ---
    def add_user(self, telegram_id, username=None, full_name=None, phone_number=None, balance=0, banned=False, test_subscription=True, comment=None):
        """Add a new user to the database."""
        if not self.conn:
            logger.error("No database connection available.")
            return False

        try:
            cur = self.conn.cursor()
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            updated_at = created_at
            cur.execute("""
                INSERT INTO users (telegram_id, username, full_name, phone_number, balance, created_at, updated_at, banned, test_subscription, comment)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (telegram_id, username, full_name, phone_number, balance, created_at, updated_at, banned, test_subscription, comment))
            self.conn.commit()
            logger.info(f"User {telegram_id} added successfully.")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error adding user {telegram_id}: {e}")
            return False

    def find_user(self, telegram_id=None):
        """Find a user by telegram_id."""
        if not self.conn:
            logger.error("No database connection available.")
            return None

        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
            result = cur.fetchall()
            if result:
                # Convert to list of dictionaries
                column_names = [description[0] for description in cur.description]
                return [dict(zip(column_names, row)) for row in result]
            return None
        except sqlite3.Error as e:
            logger.error(f"Error finding user {telegram_id}: {e}")
            return None

    def select_users(self):
        """Select all users."""
        if not self.conn:
            logger.error("No database connection available.")
            return None

        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM users")
            result = cur.fetchall()
            if result:
                # Convert to list of dictionaries
                column_names = [description[0] for description in cur.description]
                return [dict(zip(column_names, row)) for row in result]
            return None
        except sqlite3.Error as e:
            logger.error(f"Error selecting users: {e}")
            return None

    def edit_user(self, telegram_id, **kwargs):
        """Edit user information."""
        if not self.conn:
            logger.error("No database connection available.")
            return False

        if not kwargs:
            logger.warning("No fields to update for user.")
            return False

        try:
            cur = self.conn.cursor()
            # Build the SET clause dynamically
            set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values())
            values.append(telegram_id)  # For the WHERE clause
            query = f"UPDATE users SET {set_clause}, updated_at = ? WHERE telegram_id = ?"
            values.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))  # updated_at
            cur.execute(query, values)
            self.conn.commit()
            if cur.rowcount > 0:
                logger.info(f"User {telegram_id} updated successfully.")
                return True
            else:
                logger.warning(f"No user found with telegram_id {telegram_id} to update.")
                return False
        except sqlite3.Error as e:
            logger.error(f"Error editing user {telegram_id}: {e}")
            return False

    def delete_user(self, telegram_id):
        """Delete a user by telegram_id."""
        if not self.conn:
            logger.error("No database connection available.")
            return False

        try:
            cur = self.conn.cursor()
            cur.execute("DELETE FROM users WHERE telegram_id = ?", (telegram_id,))
            self.conn.commit()
            if cur.rowcount > 0:
                logger.info(f"User {telegram_id} deleted successfully.")
                return True
            else:
                logger.warning(f"No user found with telegram_id {telegram_id} to delete.")
                return False
        except sqlite3.Error as e:
            logger.error(f"Error deleting user {telegram_id}: {e}")
            return False

    # --- Server Management Methods ---
    def add_server(self, title, url, user_limit=None, status=True, comment=None):
        """Add a new server to the database."""
        if not self.conn:
            logger.error("No database connection available.")
            return False

        try:
            cur = self.conn.cursor()
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            updated_at = created_at
            cur.execute("""
                INSERT INTO servers (title, url, user_limit, status, comment, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (title, url, user_limit, status, comment, created_at, updated_at))
            self.conn.commit()
            server_id = cur.lastrowid
            logger.info(f"Server '{title}' (ID: {server_id}) added successfully.")
            return server_id
        except sqlite3.Error as e:
            logger.error(f"Error adding server '{title}': {e}")
            return False

    def find_server(self, id=None):
        """Find a server by id."""
        if not self.conn:
            logger.error("No database connection available.")
            return None

        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM servers WHERE id = ?", (id,))
            result = cur.fetchall()
            if result:
                # Convert to list of dictionaries
                column_names = [description[0] for description in cur.description]
                return [dict(zip(column_names, row)) for row in result]
            return None
        except sqlite3.Error as e:
            logger.error(f"Error finding server {id}: {e}")
            return None

    def select_servers(self):
        """Select all servers."""
        if not self.conn:
            logger.error("No database connection available.")
            return None

        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM servers")
            result = cur.fetchall()
            if result:
                # Convert to list of dictionaries
                column_names = [description[0] for description in cur.description]
                return [dict(zip(column_names, row)) for row in result]
            return None
        except sqlite3.Error as e:
            logger.error(f"Error selecting servers: {e}")
            return None

    def edit_server(self, id, **kwargs):
        """Edit server information."""
        if not self.conn:
            logger.error("No database connection available.")
            return False

        if not kwargs:
            logger.warning("No fields to update for server.")
            return False

        try:
            cur = self.conn.cursor()
            # Build the SET clause dynamically
            set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values())
            values.append(id)  # For the WHERE clause
            query = f"UPDATE servers SET {set_clause}, updated_at = ? WHERE id = ?"
            values.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))  # updated_at
            cur.execute(query, values)
            self.conn.commit()
            if cur.rowcount > 0:
                logger.info(f"Server {id} updated successfully.")
                return True
            else:
                logger.warning(f"No server found with id {id} to update.")
                return False
        except sqlite3.Error as e:
            logger.error(f"Error editing server {id}: {e}")
            return False

    def delete_server(self, id):
        """Delete a server by id."""
        if not self.conn:
            logger.error("No database connection available.")
            return False

        try:
            cur = self.conn.cursor()
            cur.execute("DELETE FROM servers WHERE id = ?", (id,))
            self.conn.commit()
            if cur.rowcount > 0:
                logger.info(f"Server {id} deleted successfully.")
                return True
            else:
                logger.warning(f"No server found with id {id} to delete.")
                return False
        except sqlite3.Error as e:
            logger.error(f"Error deleting server {id}: {e}")
            return False

    # --- Plan Management Methods ---
    def add_plan(self, name, size_gb, days, price, server_id, status=True, description=None):
        """Add a new plan to the database."""
        if not self.conn:
            logger.error("No database connection available.")
            return False

        try:
            cur = self.conn.cursor()
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            updated_at = created_at
            cur.execute("""
                INSERT INTO plans (name, size_gb, days, price, server_id, status, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, size_gb, days, price, server_id, status, description, created_at, updated_at))
            self.conn.commit()
            plan_id = cur.lastrowid
            logger.info(f"Plan '{name}' (ID: {plan_id}) added successfully.")
            return plan_id
        except sqlite3.Error as e:
            logger.error(f"Error adding plan '{name}': {e}")
            return False

    def find_plan(self, id=None, server_id=None):
        """Find plans by id or server_id."""
        if not self.conn:
            logger.error("No database connection available.")
            return None

        try:
            cur = self.conn.cursor()
            if id is not None:
                cur.execute("SELECT * FROM plans WHERE id = ?", (id,))
            elif server_id is not None:
                cur.execute("SELECT * FROM plans WHERE server_id = ?", (server_id,))
            else:
                return None
            result = cur.fetchall()
            if result:
                # Convert to list of dictionaries
                column_names = [description[0] for description in cur.description]
                return [dict(zip(column_names, row)) for row in result]
            return None
        except sqlite3.Error as e:
            logger.error(f"Error finding plan: {e}")
            return None

    def select_plans(self):
        """Select all plans."""
        if not self.conn:
            logger.error("No database connection available.")
            return None

        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM plans")
            result = cur.fetchall()
            if result:
                # Convert to list of dictionaries
                column_names = [description[0] for description in cur.description]
                return [dict(zip(column_names, row)) for row in result]
            return None
        except sqlite3.Error as e:
            logger.error(f"Error selecting plans: {e}")
            return None

    def edit_plan(self, id, **kwargs):
        """Edit plan information."""
        if not self.conn:
            logger.error("No database connection available.")
            return False

        if not kwargs:
            logger.warning("No fields to update for plan.")
            return False

        try:
            cur = self.conn.cursor()
            # Build the SET clause dynamically
            set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values())
            values.append(id)  # For the WHERE clause
            query = f"UPDATE plans SET {set_clause}, updated_at = ? WHERE id = ?"
            values.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))  # updated_at
            cur.execute(query, values)
            self.conn.commit()
            if cur.rowcount > 0:
                logger.info(f"Plan {id} updated successfully.")
                return True
            else:
                logger.warning(f"No plan found with id {id} to update.")
                return False
        except sqlite3.Error as e:
            logger.error(f"Error editing plan {id}: {e}")
            return False

    def delete_plan(self, id):
        """Delete a plan by id."""
        if not self.conn:
            logger.error("No database connection available.")
            return False

        try:
            cur = self.conn.cursor()
            cur.execute("DELETE FROM plans WHERE id = ?", (id,))
            self.conn.commit()
            if cur.rowcount > 0:
                logger.info(f"Plan {id} deleted successfully.")
                return True
            else:
                logger.warning(f"No plan found with id {id} to delete.")
                return False
        except sqlite3.Error as e:
            logger.error(f"Error deleting plan {id}: {e}")
            return False

    # --- Order Management Methods ---
    def add_order(self, telegram_id, plan_id, server_id, uuid, price, status=True):
        """Add a new order to the database."""
        if not self.conn:
            logger.error("No database connection available.")
            return False

        try:
            cur = self.conn.cursor()
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            updated_at = created_at
            cur.execute("""
                INSERT INTO orders (telegram_id, plan_id, server_id, uuid, price, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (telegram_id, plan_id, server_id, uuid, price, status, created_at, updated_at))
            self.conn.commit()
            order_id = cur.lastrowid
            logger.info(f"Order (ID: {order_id}) for user {telegram_id} added successfully.")
            return order_id
        except sqlite3.Error as e:
            logger.error(f"Error adding order for user {telegram_id}: {e}")
            return False

    def find_order(self, id=None, telegram_id=None):
        """Find orders by id or telegram_id."""
        if not self.conn:
            logger.error("No database connection available.")
            return None

        try:
            cur = self.conn.cursor()
            if id is not None:
                cur.execute("SELECT * FROM orders WHERE id = ?", (id,))
            elif telegram_id is not None:
                cur.execute("SELECT * FROM orders WHERE telegram_id = ?", (telegram_id,))
            else:
                return None
            result = cur.fetchall()
            if result:
                # Convert to list of dictionaries
                column_names = [description[0] for description in cur.description]
                return [dict(zip(column_names, row)) for row in result]
            return None
        except sqlite3.Error as e:
            logger.error(f"Error finding order: {e}")
            return None

    def select_orders(self):
        """Select all orders."""
        if not self.conn:
            logger.error("No database connection available.")
            return None

        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM orders")
            result = cur.fetchall()
            if result:
                # Convert to list of dictionaries
                column_names = [description[0] for description in cur.description]
                return [dict(zip(column_names, row)) for row in result]
            return None
        except sqlite3.Error as e:
            logger.error(f"Error selecting orders: {e}")
            return None

    # --- Payment Management Methods ---
    def add_payment(self, telegram_id, payment_amount, approved=None, authority=None, payment_method="Card", photo_path=None):
        """Add a new payment to the database."""
        if not self.conn:
            logger.error("No database connection available.")
            return False

        try:
            cur = self.conn.cursor()
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            updated_at = created_at
            cur.execute("""
                INSERT INTO payments (telegram_id, payment_amount, approved, authority, payment_method, photo_path, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (telegram_id, payment_amount, approved, authority, payment_method, photo_path, created_at, updated_at))
            self.conn.commit()
            payment_id = cur.lastrowid
            logger.info(f"Payment (ID: {payment_id}) for user {telegram_id} added successfully.")
            return payment_id
        except sqlite3.Error as e:
            logger.error(f"Error adding payment for user {telegram_id}: {e}")
            return False

    def find_payment(self, id=None, telegram_id=None):
        """Find payments by id or telegram_id."""
        if not self.conn:
            logger.error("No database connection available.")
            return None

        try:
            cur = self.conn.cursor()
            if id is not None:
                cur.execute("SELECT * FROM payments WHERE id = ?", (id,))
            elif telegram_id is not None:
                cur.execute("SELECT * FROM payments WHERE telegram_id = ?", (telegram_id,))
            else:
                return None
            result = cur.fetchall()
            if result:
                # Convert to list of dictionaries
                column_names = [description[0] for description in cur.description]
                return [dict(zip(column_names, row)) for row in result]
            return None
        except sqlite3.Error as e:
            logger.error(f"Error finding payment: {e}")
            return None

    def select_payments(self):
        """Select all payments."""
        if not self.conn:
            logger.error("No database connection available.")
            return None

        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM payments")
            result = cur.fetchall()
            if result:
                # Convert to list of dictionaries
                column_names = [description[0] for description in cur.description]
                return [dict(zip(column_names, row)) for row in result]
            return None
        except sqlite3.Error as e:
            logger.error(f"Error selecting payments: {e}")
            return None

    def edit_payment(self, id, **kwargs):
        """Edit payment information."""
        if not self.conn:
            logger.error("No database connection available.")
            return False

        if not kwargs:
            logger.warning("No fields to update for payment.")
            return False

        try:
            cur = self.conn.cursor()
            # Build the SET clause dynamically
            set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values())
            values.append(id)  # For the WHERE clause
            query = f"UPDATE payments SET {set_clause}, updated_at = ? WHERE id = ?"
            values.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))  # updated_at
            cur.execute(query, values)
            self.conn.commit()
            if cur.rowcount > 0:
                logger.info(f"Payment {id} updated successfully.")
                return True
            else:
                logger.warning(f"No payment found with id {id} to update.")
                return False
        except sqlite3.Error as e:
            logger.error(f"Error editing payment {id}: {e}")
            return False

    # --- Non-Order Subscription Management Methods ---
    def add_non_order_subscription(self, telegram_id, uuid, server_id):
        """Add a new non-order subscription to the database."""
        if not self.conn:
            logger.error("No database connection available.")
            return False

        try:
            cur = self.conn.cursor()
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            updated_at = created_at
            cur.execute("""
                INSERT INTO non_order_subscriptions (telegram_id, uuid, server_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (telegram_id, uuid, server_id, created_at, updated_at))
            self.conn.commit()
            subscription_id = cur.lastrowid
            logger.info(f"Non-order subscription (ID: {subscription_id}) for user {telegram_id} added successfully.")
            return subscription_id
        except sqlite3.Error as e:
            logger.error(f"Error adding non-order subscription for user {telegram_id}: {e}")
            return False

    def find_non_order_subscription(self, telegram_id=None, uuid=None):
        """Find non-order subscriptions by telegram_id or uuid."""
        if not self.conn:
            logger.error("No database connection available.")
            return None

        try:
            cur = self.conn.cursor()
            if telegram_id is not None:
                cur.execute("SELECT * FROM non_order_subscriptions WHERE telegram_id = ?", (telegram_id,))
            elif uuid is not None:
                cur.execute("SELECT * FROM non_order_subscriptions WHERE uuid = ?", (uuid,))
            else:
                return None
            result = cur.fetchall()
            if result:
                # Convert to list of dictionaries
                column_names = [description[0] for description in cur.description]
                return [dict(zip(column_names, row)) for row in result]
            return None
        except sqlite3.Error as e:
            logger.error(f"Error finding non-order subscription: {e}")
            return None

    # --- Test Subscription Management Methods ---
    def add_test_subscription(self, telegram_id, uuid, server_id):
        """Add a new test subscription to the database."""
        if not self.conn:
            logger.error("No database connection available.")
            return False

        try:
            cur = self.conn.cursor()
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            updated_at = created_at
            cur.execute("""
                INSERT INTO test_subscriptions (telegram_id, uuid, server_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (telegram_id, uuid, server_id, created_at, updated_at))
            self.conn.commit()
            subscription_id = cur.lastrowid
            logger.info(f"Test subscription (ID: {subscription_id}) for user {telegram_id} added successfully.")
            return subscription_id
        except sqlite3.Error as e:
            logger.error(f"Error adding test subscription for user {telegram_id}: {e}")
            return False

    def find_test_subscription(self, telegram_id=None):
        """Find test subscriptions by telegram_id."""
        if not self.conn:
            logger.error("No database connection available.")
            return None

        try:
            cur = self.conn.cursor()
            if telegram_id is not None:
                cur.execute("SELECT * FROM test_subscriptions WHERE telegram_id = ?", (telegram_id,))
            else:
                return None
            result = cur.fetchall()
            if result:
                # Convert to list of dictionaries
                column_names = [description[0] for description in cur.description]
                return [dict(zip(column_names, row)) for row in result]
            return None
        except sqlite3.Error as e:
            logger.error(f"Error finding test subscription: {e}")
            return None

    # --- Event Management Methods ---
    def add_event(self, telegram_id, event_type, details=None):
        """Add a new event to the database."""
        if not self.conn:
            logger.error("No database connection available.")
            return False

        try:
            cur = self.conn.cursor()
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur.execute("""
                INSERT INTO events (telegram_id, event_type, details, created_at)
                VALUES (?, ?, ?, ?)
            """, (telegram_id, event_type, details, created_at))
            self.conn.commit()
            event_id = cur.lastrowid
            logger.info(f"Event (ID: {event_id}) for user {telegram_id} added successfully.")
            return event_id
        except sqlite3.Error as e:
            logger.error(f"Error adding event for user {telegram_id}: {e}")
            return False

    # --- Configuration Management Methods ---
    def select_int_config(self):
        """Select all integer configurations."""
        if not self.conn:
            logger.error("No database connection available.")
            return None

        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM int_config")
            result = cur.fetchall()
            if result:
                # Convert to list of dictionaries
                column_names = [description[0] for description in cur.description]
                return [dict(zip(column_names, row)) for row in result]
            return None
        except sqlite3.Error as e:
            logger.error(f"Error selecting integer configurations: {e}")
            return None

    def select_str_config(self):
        """Select all string configurations."""
        if not self.conn:
            logger.error("No database connection available.")
            return None

        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM str_config")
            result = cur.fetchall()
            if result:
                # Convert to list of dictionaries
                column_names = [description[0] for description in cur.description]
                return [dict(zip(column_names, row)) for row in result]
            return None
        except sqlite3.Error as e:
            logger.error(f"Error selecting string configurations: {e}")
            return None

    def select_bool_config(self):
        """Select all boolean configurations."""
        if not self.conn:
            logger.error("No database connection available.")
            return None

        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM bool_config")
            result = cur.fetchall()
            if result:
                # Convert to list of dictionaries
                column_names = [description[0] for description in cur.description]
                return [dict(zip(column_names, row)) for row in result]
            return None
        except sqlite3.Error as e:
            logger.error(f"Error selecting boolean configurations: {e}")
            return None

    def edit_int_config(self, key, value):
        """Edit an integer configuration value."""
        if not self.conn:
            logger.error("No database connection available.")
            return False

        try:
            cur = self.conn.cursor()
            cur.execute("UPDATE int_config SET value = ? WHERE key = ?", (value, key))
            self.conn.commit()
            if cur.rowcount > 0:
                logger.info(f"Integer config '{key}' updated successfully.")
                return True
            else:
                # If key doesn't exist, insert it
                cur.execute("INSERT OR IGNORE INTO int_config (key, value) VALUES (?, ?)", (key, value))
                self.conn.commit()
                if cur.rowcount > 0:
                    logger.info(f"Integer config '{key}' inserted successfully.")
                    return True
                else:
                    logger.warning(f"Failed to update or insert integer config '{key}'.")
                    return False
        except sqlite3.Error as e:
            logger.error(f"Error editing integer config '{key}': {e}")
            return False

    def edit_str_config(self, key, value):
        """Edit a string configuration value."""
        if not self.conn:
            logger.error("No database connection available.")
            return False

        try:
            cur = self.conn.cursor()
            cur.execute("UPDATE str_config SET value = ? WHERE key = ?", (value, key))
            self.conn.commit()
            if cur.rowcount > 0:
                logger.info(f"String config '{key}' updated successfully.")
                return True
            else:
                # If key doesn't exist, insert it
                cur.execute("INSERT OR IGNORE INTO str_config (key, value) VALUES (?, ?)", (key, value))
                self.conn.commit()
                if cur.rowcount > 0:
                    logger.info(f"String config '{key}' inserted successfully.")
                    return True
                else:
                    logger.warning(f"Failed to update or insert string config '{key}'.")
                    return False
        except sqlite3.Error as e:
            logger.error(f"Error editing string config '{key}': {e}")
            return False

    def edit_bool_config(self, key, value):
        """Edit a boolean configuration value."""
        if not self.conn:
            logger.error("No database connection available.")
            return False

        try:
            cur = self.conn.cursor()
            cur.execute("UPDATE bool_config SET value = ? WHERE key = ?", (value, key))
            self.conn.commit()
            if cur.rowcount > 0:
                logger.info(f"Boolean config '{key}' updated successfully.")
                return True
            else:
                # If key doesn't exist, insert it
                cur.execute("INSERT OR IGNORE INTO bool_config (key, value) VALUES (?, ?)", (key, value))
                self.conn.commit()
                if cur.rowcount > 0:
                    logger.info(f"Boolean config '{key}' inserted successfully.")
                    return True
                else:
                    logger.warning(f"Failed to update or insert boolean config '{key}'.")
                    return False
        except sqlite3.Error as e:
            logger.error(f"Error editing boolean config '{key}': {e}")
            return False

    # --- New Feature Methods ---

    # --- Referral System Methods ---
    def add_referral(self, referrer_id, referred_id):
        """Add a new referral relationship."""
        if not self.conn:
            logger.error("No database connection available.")
            return False

        try:
            cur = self.conn.cursor()
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur.execute("""
                INSERT OR IGNORE INTO referrals (referrer_id, referred_id, created_at)
                VALUES (?, ?, ?)
            """, (referrer_id, referred_id, created_at))
            self.conn.commit()
            if cur.rowcount > 0:
                referral_id = cur.lastrowid
                logger.info(f"Referral (ID: {referral_id}) from user {referrer_id} to {referred_id} added successfully.")
                return referral_id
            else:
                logger.info(f"Referral from user {referrer_id} to {referred_id} already exists.")
                return True  # Already exists, which is also a success
        except sqlite3.Error as e:
            logger.error(f"Error adding referral from {referrer_id} to {referred_id}: {e}")
            return False

    def get_referrals_by_referrer(self, referrer_id):
        """Get all referrals made by a specific user."""
        if not self.conn:
            logger.error("No database connection available.")
            return None

        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM referrals WHERE referrer_id = ?", (referrer_id,))
            result = cur.fetchall()
            if result:
                # Convert to list of dictionaries
                column_names = [description[0] for description in cur.description]
                return [dict(zip(column_names, row)) for row in result]
            return None
        except sqlite3.Error as e:
            logger.error(f"Error getting referrals for user {referrer_id}: {e}")
            return None

    def get_referral_commission(self, user_id):
        """Get total commission earned by a user through referrals."""
        if not self.conn:
            logger.error("No database connection available.")
            return 0

        try:
            cur = self.conn.cursor()
            cur.execute("SELECT SUM(commission) FROM referrals WHERE referrer_id = ?", (user_id,))
            result = cur.fetchone()
            return result[0] if result[0] else 0
        except sqlite3.Error as e:
            logger.error(f"Error getting referral commission for user {user_id}: {e}")
            return 0

    # --- Coupon Methods ---
    def add_coupon(self, code, discount_type, discount_value, usage_limit=None, expiry_date=None, is_active=True):
        """Add a new coupon."""
        if not self.conn:
            logger.error("No database connection available.")
            return False

        try:
            cur = self.conn.cursor()
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            updated_at = created_at
            cur.execute("""
                INSERT INTO coupons (code, discount_type, discount_value, usage_limit, expiry_date, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (code, discount_type, discount_value, usage_limit, expiry_date, is_active, created_at, updated_at))
            self.conn.commit()
            coupon_id = cur.lastrowid
            logger.info(f"Coupon '{code}' (ID: {coupon_id}) added successfully.")
            return coupon_id
        except sqlite3.Error as e:
            logger.error(f"Error adding coupon '{code}': {e}")
            return False

    def find_coupon_by_code(self, code):
        """Find a coupon by its code."""
        if not self.conn:
            logger.error("No database connection available.")
            return None

        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM coupons WHERE code = ?", (code,))
            result = cur.fetchone()
            if result:
                # Convert to dictionary
                column_names = [description[0] for description in cur.description]
                return dict(zip(column_names, result))
            return None
        except sqlite3.Error as e:
            logger.error(f"Error finding coupon '{code}': {e}")
            return None

    def use_coupon(self, coupon_id, user_id):
        """Record that a user has used a coupon."""
        if not self.conn:
            logger.error("No database connection available.")
            return False

        try:
            cur = self.conn.cursor()
            used_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur.execute("""
                INSERT INTO coupon_usage (coupon_id, user_id, used_at)
                VALUES (?, ?, ?)
            """, (coupon_id, user_id, used_at))
            self.conn.commit()
            
            # Increment the used_count in coupons table
            cur.execute("UPDATE coupons SET used_count = used_count + 1 WHERE id = ?", (coupon_id,))
            self.conn.commit()
            
            logger.info(f"Coupon {coupon_id} used by user {user_id}.")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error recording coupon usage for coupon {coupon_id} by user {user_id}: {e}")
            return False

    def is_coupon_used_by_user(self, coupon_id, user_id):
        """Check if a user has already used a specific coupon."""
        if not self.conn:
            logger.error("No database connection available.")
            return False

        try:
            cur = self.conn.cursor()
            cur.execute("SELECT 1 FROM coupon_usage WHERE coupon_id = ? AND user_id = ?", (coupon_id, user_id))
            result = cur.fetchone()
            return result is not None
        except sqlite3.Error as e:
            logger.error(f"Error checking coupon usage for coupon {coupon_id} by user {user_id}: {e}")
            return False

    # --- Online Payment Methods ---
    def add_online_payment(self, payment_id, gateway, transaction_id=None, callback_url=None, status="pending"):
        """Add a new online payment transaction."""
        if not self.conn:
            logger.error("No database connection available.")
            return False

        try:
            cur = self.conn.cursor()
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            updated_at = created_at
            cur.execute("""
                INSERT INTO online_payments (payment_id, gateway, transaction_id, callback_url, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (payment_id, gateway, transaction_id, callback_url, status, created_at, updated_at))
            self.conn.commit()
            online_payment_id = cur.lastrowid
            logger.info(f"Online payment (ID: {online_payment_id}) for payment {payment_id} added successfully.")
            return online_payment_id
        except sqlite3.Error as e:
            logger.error(f"Error adding online payment for payment {payment_id}: {e}")
            return False

    def update_online_payment_status(self, payment_id, status, transaction_id=None):
        """Update the status of an online payment."""
        if not self.conn:
            logger.error("No database connection available.")
            return False

        try:
            cur = self.conn.cursor()
            updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if transaction_id:
                cur.execute("""
                    UPDATE online_payments 
                    SET status = ?, transaction_id = ?, updated_at = ? 
                    WHERE payment_id = ?
                """, (status, transaction_id, updated_at, payment_id))
            else:
                cur.execute("""
                    UPDATE online_payments 
                    SET status = ?, updated_at = ? 
                    WHERE payment_id = ?
                """, (status, updated_at, payment_id))
            self.conn.commit()
            if cur.rowcount > 0:
                logger.info(f"Online payment {payment_id} status updated to '{status}' successfully.")
                return True
            else:
                logger.warning(f"No online payment found with payment_id {payment_id} to update.")
                return False
        except sqlite3.Error as e:
            logger.error(f"Error updating online payment {payment_id} status: {e}")
            return False

    # --- Backup and Restore Methods ---
    def backup_to_json(self, backup_dir):
        """Backup the database to a JSON file."""
        if not self.conn:
            logger.error("No database connection available.")
            return None

        try:
            backup_data = {}
            
            # Backup all tables
            tables = [
                'users', 'servers', 'plans', 'orders', 'payments', 'non_order_subscriptions',
                'test_subscriptions', 'events', 'int_config', 'str_config', 'bool_config',
                'referrals', 'coupons', 'coupon_usage', 'online_payments'
            ]
            
            for table in tables:
                cur = self.conn.cursor()
                cur.execute(f"SELECT * FROM {table}")
                rows = cur.fetchall()
                if rows:
                    column_names = [description[0] for description in cur.description]
                    backup_data[table] = [dict(zip(column_names, row)) for row in rows]
                else:
                    backup_data[table] = []
            
            return backup_data
        except sqlite3.Error as e:
            logger.error(f"Error backing up database: {e}")
            return None

    def close_connection(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed.")

# Create a global instance of the UserDBManager
# The database file will be in the same directory as this script
# You might want to change this to a more specific path
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Database', 'hidyBot.db')
USERS_DB = UserDBManager(DB_PATH)
