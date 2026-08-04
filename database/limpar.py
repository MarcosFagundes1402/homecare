import sqlite3

conexao = sqlite3.connect("homecare.db")
cursor = conexao.cursor()

cursor.execute("DELETE FROM usuarios")

conexao.commit()
conexao.close()

print("Todos os usuários foram removidos.")