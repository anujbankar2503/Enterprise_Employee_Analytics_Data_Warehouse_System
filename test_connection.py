import mysql.connector

from src.config import database_config

conn = mysql.connector.connect(**{k: v for k, v in database_config("mysql").items()
                                  if k != "database"})

cursor = conn.cursor()
cursor.execute("SHOW DATABASES")
for (db,) in cursor.fetchall():
    print(db)

cursor.close()
conn.close()