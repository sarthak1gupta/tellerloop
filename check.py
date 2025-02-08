
import sqlite3

DATABASE = 'lan_monitoring.db'

def check_schema():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    
    # Get the schema of the 'messages' table
    cur.execute("PRAGMA table_info(messages)")
    columns = cur.fetchall()
    
    for column in columns:
        print(column)
    
    conn.close()

if __name__ == '__main__':
    check_schema()
