import sqlite3

DATABASE = 'lan_monitoring.db'  # Path to your SQLite database file

def add_columns():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    
    # Add new columns if they don't already exist
    try:
        cur.execute("ALTER TABLE messages ADD COLUMN cp1 BOOLEAN DEFAULT 0")
    except sqlite3.OperationalError:
        print("Column 'cp1' already exists or other error occurred.")
    
    try:
        cur.execute("ALTER TABLE messages ADD COLUMN cp2 BOOLEAN DEFAULT 0")
    except sqlite3.OperationalError:
        print("Column 'cp2' already exists or other error occurred.")
    
    try:
        cur.execute("ALTER TABLE messages ADD COLUMN cp3 BOOLEAN DEFAULT 0")
    except sqlite3.OperationalError:
        print("Column 'cp3' already exists or other error occurred.")
    
    try:
        cur.execute("ALTER TABLE messages ADD COLUMN cp4 BOOLEAN DEFAULT 0")
    except sqlite3.OperationalError:
        print("Column 'cp4' already exists or other error occurred.")
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    add_columns()
