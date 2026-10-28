import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

conn=mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)

cursor = conn.cursor()
cursor.execute("SHOW DATABASES")
for (db,) in cursor.fetchall():
    print(db)

cursor.close()
conn.close()