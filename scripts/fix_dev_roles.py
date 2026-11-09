import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database

conn = database.get_connection()
conn.execute("UPDATE users SET role = 'Developer' WHERE username IN ('dev1', 'dev2', 'dev3')")
conn.commit()
conn.close()
print("Restored developer roles successfully.")
