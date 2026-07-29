from database.connect import connect


def tabela_paciente():

    conexao = connect()
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pacientes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTERGER NOT NULL,
            cpf TEXT UNIQUE,
            data_nascimento TEXT,
            tel  TEXT,
            endereco TEXT,
            obs TEXT,
            FOREIGN KEY(usuario_id)
            REFERENCES usuarios (id))
    """)

    conexao.commit()
    cursor.close()

tabela_paciente()