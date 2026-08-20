from connect import connect


def tabela_paciente():

    conexao = connect()
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pacientes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
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
    conexao.close()

def tabela_cuidadores():

    conexao = connect()
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cuidadores(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            cpf TEXT UNIQUE,
            data_nascimento TEXT,
            tel  TEXT,
            endereco TEXT,
            obs TEXT,
            status TEXT,
            FOREIGN KEY(usuario_id)
            REFERENCES usuarios (id))
    """)

    conexao.commit()

    print("Tabela cuidadores criada com sucesso")

    cursor.close()
    conexao.close()

def cuidadores_pacientes():

    conexao = connect()
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cuidadores_pacientes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cuidador_id INTEGER NOT NULL,
        paciente_id INTEGER NOT NULL,
        FOREIGN KEY(cuidador_id) REFERENCES cuidadores(id),
        FOREIGN KEY(paciente_id) REFERENCES pacientes(id))
    """)

tabela_paciente()
tabela_cuidadores()
cuidadores_pacientes()