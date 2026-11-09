import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database

conn = database.get_connection()
conn.execute("UPDATE users SET full_name = 'Naveen (QA Director)' WHERE username = 'admin'")
conn.commit()
conn.close()
print("Successfully updated admin full_name to 'Naveen (QA Director)'")
