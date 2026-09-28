from connect import connect

connection = connect()
cursor = connection.cursor()

cursor.execute("DROP TABLE IF EXISTS administracao_medicamentos")
cursor.execute("DROP TABLE IF EXISTS relatorios_diarios")
cursor.execute("DROP TABLE IF EXISTS cuidadores_pacientes")
cursor.execute("DROP TABLE IF EXISTS medicamentos")
cursor.execute("DROP TABLE IF EXISTS cuidadores")
cursor.execute("DROP TABLE IF EXISTS pacientes")
cursor.execute("DROP TABLE IF EXISTS usuarios")

connection.commit()

print("Tabelas removidas com sucesso.")

cursor.close()
connection.close()
