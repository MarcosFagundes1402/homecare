import sqlite3

def connect():
    conexao =  sqlite3.connect("database/homecare.db")
    conexao.row_factory = sqlite3.Row

    conexao.execute("PRAGMA foreign_keys = ON")
    
    return conexao