# update.py
# Description: Update script for the bot database and configurations.
import json
import sqlite3
import argparse
import logging
import os
from version import is_version_less, compare_versions, __version__

# Configuration
USERS_DB_LOC = os.path.join(os.getcwd(), "Database", "hidyBot.db")
LOG_LOC = os.path.join(os.getcwd(), "Logs", "update.log")

# Ensure log directory exists
os.makedirs(os.path.dirname(LOG_LOC), exist_ok=True)

# Configure logging
logging.basicConfig(
    handlers=[logging.FileHandler(filename=LOG_LOC, encoding='utf-8', mode='a')],
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def version():
    """Parse command-line arguments for the update script."""
    parser = argparse.ArgumentParser(description='Update script for Hiddify Telegram Bot')
    parser.add_argument('--current-version', type=str, help='Current version')
    parser.add_argument('--target-version', type=str, help='Target version')
    args = parser.parse_args()
    return args

def connect_db():
    """Create a database connection."""
    try:
        conn = sqlite3.connect(USERS_DB_LOC)
        # Enable foreign key constraints
        conn.execute("PRAGMA foreign_key_check")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Error connecting to database: {e}")
        return None

def drop_columns_from_table(conn, table_name, columns_to_drop):
    """
    Drop specified columns from a table.
    Note: SQLite doesn't support DROP COLUMN directly, so we recreate the table.
    """
    try:
        cur = conn.cursor()
        
        # Get table info
        cur.execute(f"PRAGMA table_info({table_name});")
        columns_info = cur.fetchall()
        
        # Create list of columns to keep
        columns_to_keep = [col[1] for col in columns_info if col[1] not in columns_to_drop]
        
        if not columns_to_keep:
            logger.warning(f"No columns to keep in table {table_name}. Skipping drop operation.")
            return False
            
        columns_to_keep_str = ', '.join(columns_to_keep)
        
        # Begin transaction
        conn.execute("BEGIN TRANSACTION;")
        
        # Create new table without the columns to drop
        cur.execute(f"CREATE TABLE new_{table_name} AS SELECT {columns_to_keep_str} FROM {table_name};")
        
        # Drop the original table
        cur.execute(f"DROP TABLE {table_name};")
        
        # Get original table schema (to preserve constraints, keys, etc.)
        # This is a simplified approach. For complex tables, you might need to store the schema.
        # For now, we'll recreate with basic structure.
        cur.execute(f"ALTER TABLE new_{table_name} RENAME TO {table_name};")
        
        # Commit transaction
        conn.execute("COMMIT;")
        
        logger.info(f"Dropped columns {columns_to_drop} from table {table_name}")
        return True

    except sqlite3.Error as e:
        conn.execute("ROLLBACK;")
        logger.error(f"Database error dropping columns from {table_name}: {e}")
        return False
    except Exception as e:
        conn.execute("ROLLBACK;")
        logger.error(f"Unexpected error dropping columns from {table_name}: {e}")
        return False

def update_v4_v5(conn):
    """Update database from version 4.x to 5.0.0"""
    logger.info("Updating database from version v4 to v5")
    print("Updating database from version v4 to v5")
    
    try:
        cur = conn.cursor()
        
        # Clean up orders table
        cur.execute("DELETE FROM orders WHERE approved = 0 OR approved IS NULL")
        logger.info("Cleaned up unapproved orders")
        
        # Drop obsolete columns from orders
        drop_columns_from_table(conn, 'orders', ['payment_image', 'payment_method', 'approved'])
        
        # Drop obsolete tables
        tables_to_drop = ['owner_info', 'settings']
        for table in tables_to_drop:
            try:
                cur.execute(f"DROP TABLE IF EXISTS {table}")
                logger.info(f"Dropped table {table}")
            except sqlite3.Error as e:
                logger.warning(f"Could not drop table {table}: {e}")
        
        # Add new column to users
        try:
            cur.execute("ALTER TABLE users ADD COLUMN test_subscription BOOLEAN DEFAULT 0")
            logger.info("Added test_subscription column to users table")
        except sqlite3.Error as e:
            if "duplicate column name" in str(e).lower():
                logger.info("Column test_subscription already exists in users table")
            else:
                logger.error(f"Error adding test_subscription column: {e}")
        
        # Migrate config.json to database if it exists
        CONF_LOC = os.path.join(os.getcwd(), "config.json")
        if os.path.exists(CONF_LOC):
            try:
                with open(CONF_LOC, "r") as f:
                    config = json.load(f)
                
                # Create str_config table if not exists
                cur.execute("""CREATE TABLE IF NOT EXISTS str_config (
                    key TEXT PRIMARY KEY, 
                    value TEXT
                )""")
                
                # Insert config values
                config_map = {
                    "bot_admin_id": json.dumps(config.get("admin_id", [])),
                    "bot_token_admin": config.get("token", ""),
                    "bot_token_client": config.get("client_token", ""),
                    "bot_lang": config.get("lang", "FA")
                }
                
                for key, value in config_map.items():
                    cur.execute(
                        "INSERT OR REPLACE INTO str_config (key, value) VALUES (?, ?)",
                        (key, value)
                    )
                
                # Create servers table if not exists and insert server
                cur.execute("""CREATE TABLE IF NOT EXISTS servers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    title TEXT,
                    description TEXT,
                    default_server BOOLEAN NOT NULL DEFAULT 0,
                    user_limit INTEGER,
                    status BOOLEAN DEFAULT 1
                )""")
                
                server_url = config.get("url", "")
                if server_url:
                    cur.execute("""INSERT OR IGNORE INTO servers 
                        (url, title, default_server, user_limit, status) 
                        VALUES (?, ?, ?, ?, ?)""",
                        (server_url, "Main Server", True, 2000, True)
                    )
                
                conn.commit()
                logger.info("Migrated config.json to database")
                
                # Remove old config file
                os.remove(CONF_LOC)
                logger.info("Removed old config.json file")
                
            except Exception as e:
                logger.error(f"Error migrating config.json: {e}")
        
        conn.commit()
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Database error in update_v4_v5: {e}")
        conn.rollback()
        return False
    except Exception as e:
        logger.error(f"Unexpected error in update_v4_v5: {e}")
        conn.rollback()
        return False

def update_v5_1_0_to_v5_5_0(conn):
    """Update database from version 5.1.0 to 5.5.0"""
    logger.info("Updating database from version v5.1.0 to v5.5.0")
    print("Updating database from version v5.1.0 to v5.5.0")
    
    try:
        cur = conn.cursor()
        
        # Add server_id columns to various tables
        tables_columns = [
            ('plans', 'server_id'),
            ('order_subscriptions', 'server_id'),
            ('non_order_subscriptions', 'server_id')
        ]
        
        for table, column in tables_columns:
            try:
                cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} INTEGER")
                cur.execute(f"UPDATE {table} SET {column} = 1 WHERE {column} IS NULL")
                logger.info(f"Added {column} column to {table} table")
            except sqlite3.Error as e:
                if "duplicate column name" in str(e).lower():
                    logger.info(f"Column {column} already exists in {table} table")
                    # Update existing NULL values
                    cur.execute(f"UPDATE {table} SET {column} = 1 WHERE {column} IS NULL")
                else:
                    logger.error(f"Error adding {column} to {table}: {e}")
        
        # Add user_limit and status to servers table
        try:
            cur.execute("ALTER TABLE servers ADD COLUMN user_limit INTEGER")
            logger.info("Added user_limit column to servers table")
        except sqlite3.Error as e:
            if "duplicate column name" not in str(e).lower():
                logger.error(f"Error adding user_limit to servers: {e}")
        
        try:
            cur.execute("ALTER TABLE servers ADD COLUMN status BOOLEAN DEFAULT 1")
            logger.info("Added status column to servers table")
        except sqlite3.Error as e:
            if "duplicate column name" not in str(e).lower():
                logger.error(f"Error adding status to servers: {e}")
        
        # Set default values for servers
        cur.execute("UPDATE servers SET user_limit = 2000 WHERE user_limit IS NULL")
        cur.execute("UPDATE servers SET status = 1 WHERE status IS NULL")
        cur.execute("UPDATE servers SET title = 'Main Server' WHERE title IS NULL")
        
        # Add full_name and username to users table
        try:
            cur.execute("ALTER TABLE users ADD COLUMN full_name TEXT NULL")
            logger.info("Added full_name column to users table")
        except sqlite3.Error as e:
            if "duplicate column name" not in str(e).lower():
                logger.error(f"Error adding full_name to users: {e}")
                
        try:
            cur.execute("ALTER TABLE users ADD COLUMN username TEXT NULL")
            logger.info("Added username column to users table")
        except sqlite3.Error as e:
            if "duplicate column name" not in str(e).lower():
                logger.error(f"Error adding username to users: {e}")
        
        # Remove user_name from payments table
        try:
            drop_columns_from_table(conn, 'payments', ['user_name'])
        except Exception as e:
            logger.error(f"Error removing user_name from payments: {e}")
        
        conn.commit()
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Database error in update_v5_1_0_to_v5_5_0: {e}")
        conn.rollback()
        return False
    except Exception as e:
        logger.error(f"Unexpected error in update_v5_1_0_to_v5_5_0: {e}")
        conn.rollback()
        return False

def update_v5_9_5_to_v6_1_0(conn):
    """Update database from version 5.9.5 to 6.1.0"""
    logger.info("Updating database from version v5.9.5 to v6.1.0")
    print("Updating database from version v5.9.5 to v6.1.0")
    
    try:
        cur = conn.cursor()
        
        # Add banned column to users table
        try:
            cur.execute("ALTER TABLE users ADD COLUMN banned BOOLEAN DEFAULT 0")
            cur.execute("UPDATE users SET banned = 0 WHERE banned IS NULL")
            logger.info("Added banned column to users table")
        except sqlite3.Error as e:
            if "duplicate column name" in str(e).lower():
                logger.info("Column banned already exists in users table")
                # Update existing NULL values
                cur.execute("UPDATE users SET banned = 0 WHERE banned IS NULL")
            else:
                logger.error(f"Error adding banned column: {e}")
        
        conn.commit()
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Database error in update_v5_9_5_to_v6_1_0: {e}")
        conn.rollback()
        return False
    except Exception as e:
        logger.error(f"Unexpected error in update_v5_9_5_to_v6_1_0: {e}")
        conn.rollback()
        return False

def update_v6_1_5_to_v6_2_0(conn):
    """Update database from version 6.1.5 to 6.2.0 - Add new features support"""
    logger.info("Updating database from version v6.1.5 to v6.2.0")
    print("Updating database from version v6.1.5 to v6.2.0")
    
    try:
        cur = conn.cursor()
        
        # Add columns for affiliate/referral system
        try:
            # Create referrals table for affiliate system
            cur.execute("""CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER NOT NULL,
                referred_id INTEGER NOT NULL,
                commission INTEGER DEFAULT 0,
                created_at TEXT,
                FOREIGN KEY (referrer_id) REFERENCES users (telegram_id),
                FOREIGN KEY (referred_id) REFERENCES users (telegram_id),
                UNIQUE(referrer_id, referred_id)
            )""")
            logger.info("Created referrals table for affiliate system")
        except sqlite3.Error as e:
            logger.error(f"Error creating referrals table: {e}")
        
        try:
            # Add referral_code to users table
            cur.execute("ALTER TABLE users ADD COLUMN referral_code TEXT UNIQUE")
            logger.info("Added referral_code column to users table")
        except sqlite3.Error as e:
            if "duplicate column name" not in str(e).lower():
                logger.error(f"Error adding referral_code to users: {e}")
        
        # Add columns for coupon system
        try:
            # Create coupons table
            cur.execute("""CREATE TABLE IF NOT EXISTS coupons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                discount_type TEXT NOT NULL, -- 'percentage' or 'fixed'
                discount_value INTEGER NOT NULL, -- percentage (0-100) or fixed amount
                usage_limit INTEGER, -- NULL for unlimited
                used_count INTEGER DEFAULT 0,
                expiry_date TEXT, -- NULL for no expiry
                is_active BOOLEAN DEFAULT 1,
                created_at TEXT,
                updated_at TEXT
            )""")
            logger.info("Created coupons table")
        except sqlite3.Error as e:
            logger.error(f"Error creating coupons table: {e}")
        
        try:
            # Create coupon_usage table
            cur.execute("""CREATE TABLE IF NOT EXISTS coupon_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coupon_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                used_at TEXT,
                FOREIGN KEY (coupon_id) REFERENCES coupons (id),
                FOREIGN KEY (user_id) REFERENCES users (telegram_id)
            )""")
            logger.info("Created coupon_usage table")
        except sqlite3.Error as e:
            logger.error(f"Error creating coupon_usage table: {e}")
        
        # Add columns for online payment tracking
        try:
            # Add payment_method_details to payments table
            cur.execute("ALTER TABLE payments ADD COLUMN payment_method_details TEXT")
            logger.info("Added payment_method_details column to payments table")
        except sqlite3.Error as e:
            if "duplicate column name" not in str(e).lower():
                logger.error(f"Error adding payment_method_details to payments: {e}")
        
        try:
            # Create online_payments table for tracking online transactions
            cur.execute("""CREATE TABLE IF NOT EXISTS online_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_id INTEGER NOT NULL,
                gateway TEXT NOT NULL,
                transaction_id TEXT,
                callback_url TEXT,
                status TEXT, -- 'pending', 'completed', 'failed', 'cancelled'
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (payment_id) REFERENCES payments (id)
            )""")
            logger.info("Created online_payments table")
        except sqlite3.Error as e:
            logger.error(f"Error creating online_payments table: {e}")
        
        # Add columns for enhanced logging and statistics
        try:
            # Add last_activity to users table
            cur.execute("ALTER TABLE users ADD COLUMN last_activity TEXT")
            logger.info("Added last_activity column to users table")
        except sqlite3.Error as e:
            if "duplicate column name" not in str(e).lower():
                logger.error(f"Error adding last_activity to users: {e}")
        
        conn.commit()
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Database error in update_v6_1_5_to_v6_2_0: {e}")
        conn.rollback()
        return False
    except Exception as e:
        logger.error(f"Unexpected error in update_v6_1_5_to_v6_2_0: {e}")
        conn.rollback()
        return False

def update_database_schema(conn, current_version, target_version):
    """
    Update database schema based on version differences.
    """
    logger.info(f"Updating database schema from {current_version} to {target_version}")
    print(f"Updating database schema from {current_version} to {target_version}")
    
    try:
        # Perform sequential updates
        updates_performed = []
        
        if is_version_less(current_version, "5.0.0"):
            if update_v4_v5(conn):
                updates_performed.append("v4_to_v5")
        
        if is_version_less(current_version, "5.5.0"):
            if update_v5_1_0_to_v5_5_0(conn):
                updates_performed.append("v5.1_to_v5.5")
        
        if is_version_less(current_version, "6.1.0"):
            if update_v5_9_5_to_v6_1_0(conn):
                updates_performed.append("v5.9.5_to_v6.1.0")
        
        if is_version_less(current_version, "6.2.0"):
            if update_v6_1_5_to_v6_2_0(conn):
                updates_performed.append("v6.1.5_to_v6.2.0")
        
        if updates_performed:
            logger.info(f"Database updates completed: {', '.join(updates_performed)}")
            print(f"Database updates completed: {', '.join(updates_performed)}")
            return True
        else:
            logger.info("No database updates were necessary")
            print("No database updates were necessary")
            return True
            
    except Exception as e:
        logger.error(f"Error updating database schema: {e}")
        return False

def validate_versions(current_version, target_version):
    """
    Validate and clean version strings.
    """
    try:
        # Remove pre-release identifiers for comparison
        clean_current = current_version.split("-")[0] if "-" in current_version else current_version
        clean_target = target_version.split("-")[0] if "-" in target_version else target_version
        
        return clean_current, clean_target
    except Exception as e:
        logger.error(f"Error validating versions: {e}")
        return current_version, target_version

def main():
    """Main update function."""
    args = version()
    
    # Connect to database
    conn = connect_db()
    if not conn:
        logger.error("Failed to connect to database")
        print("❌ Failed to connect to database")
        return
    
    try:
        if args.current_version and args.target_version:
            current_version, target_version = validate_versions(args.current_version, args.target_version)
            
            logger.info(f"Update requested: {current_version} -> {target_version}")
            print(f"Update requested: {current_version} -> {target_version}")
            
            # Compare versions
            version_comparison = compare_versions(current_version, target_version)
            
            if version_comparison < 0:  # current < target
                logger.info("Update is needed")
                print("🔄 Update is needed, starting update process...")
                
                if update_database_schema(conn, current_version, target_version):
                    logger.info("Update completed successfully")
                    print("✅ Update completed successfully!")
                else:
                    logger.error("Update failed")
                    print("❌ Update failed!")
                    
            elif version_comparison > 0:  # current > target
                logger.warning("Current version is newer than target version")
                print("⚠️ Current version is newer than target version")
                
            else:  # current == target
                logger.info("Versions are identical, no update needed")
                print("ℹ️ Versions are identical, no update needed")
                
        else:
            logger.info("No version arguments provided, checking if update is needed...")
            print("ℹ️ No version arguments provided")
            # You could implement auto-detection here if needed
            
    except Exception as e:
        logger.error(f"Error in main update process: {e}")
        print(f"❌ Error in update process: {e}")
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
