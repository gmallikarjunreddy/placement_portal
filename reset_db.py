import mysql.connector
import os
from dotenv import load_dotenv
from app import init_db

# Load environment variables
load_dotenv()

# Database configuration
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'placement_portal')
}

def reset_database():
    try:
        # Connect without specifying a database
        db_config_no_db = db_config.copy()
        db_config_no_db.pop('database')
        conn = mysql.connector.connect(**db_config_no_db)
        cursor = conn.cursor()
        
        # Drop the database if it exists
        cursor.execute(f"DROP DATABASE IF EXISTS {db_config['database']}")
        print(f"Database {db_config['database']} dropped successfully")
        
        cursor.close()
        conn.close()
        
        # Reinitialize the database with new schema
        init_db()
        print(f"Database {db_config['database']} recreated successfully")
        
    except mysql.connector.Error as err:
        print(f"Error: {err}")

if __name__ == "__main__":
    reset_database() 