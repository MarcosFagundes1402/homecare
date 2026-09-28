import sqlite3

def connect():
    connection =  sqlite3.connect("database/homecare.db")
    connection.row_factory = sqlite3.Row

    connection.execute("PRAGMA foreign_keys = ON")
    
    return connection