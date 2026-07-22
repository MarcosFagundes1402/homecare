import sqlite3

def connect():
    return sqlite3.connect("database/homecare.b")