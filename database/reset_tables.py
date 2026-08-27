from connect import connect

conexao = connect()
cursor = conexao.cursor()

cursor.execute("DROP TABLE IF EXISTS cuidadores_pacientes")
cursor.execute("DROP TABLE IF EXISTS cuidadores")
cursor.execute("DROP TABLE IF EXISTS pacientes")
cursor.execute("DROP TABLE IF EXISTS usuarios")
cursor.execute("DROP TABLE IF EXISTS usuarios")
cursor.execute("DROP TABLE IF EXISTS administracao_medicamentos;")

conexao.commit()

print("Tabelas removidas com sucesso.")

cursor.close()
conexao.close()
