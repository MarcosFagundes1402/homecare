from connect import connect

connection = connect()
cursor = connection.cursor()

cursor.execute("DELETE FROM usuarios")

connection.commit()

cursor.close()
connection.close()

print("Todos os usuários foram removidos.")
