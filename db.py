import mysql.connector

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Amru@2004",
        database="judicial_system"
    )
