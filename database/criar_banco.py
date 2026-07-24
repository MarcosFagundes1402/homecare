import sqlite3

conexao = sqlite3.connect("database/homecare.db")
cursor = conexao.cursor()

comando_sqlite = """
CREATE TABLE IF NOT EXISTS usuarios (
    id  INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL,
    senha TEXT NOT NULL
)
"""

cursor.execute(comando_sqlite)
conexao.commit()
conexao.close()
print("Banco de dados criado com sucesso!")