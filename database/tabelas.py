from connect import connect


def tabela_usuarios():
    conexao = connect()
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            role TEXT NOT NULL,
            senha TEXT NOT NULL
        )
    """)

    print("Tabela de usuário criado com sucesso.")

    conexao.commit()
    cursor.close()
    conexao.close()

def tabela_paciente():

    conexao = connect()
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pacientes(
            id INTEGER PRIMARY KEY,
            nome TEXT NOT NULL,
            cpf TEXT UNIQUE,
            data_nascimento TEXT,
            tel  TEXT,
            endereco TEXT,
            obs TEXT,

            FOREIGN KEY(id)
                REFERENCES usuarios(id)
        )
    """)

    print("Tabela pacientes criada com sucesso")

    conexao.commit()
    cursor.close()
    conexao.close()

def tabela_cuidadores():

    conexao = connect()
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cuidadores(
            id INTEGER PRIMARY KEY,
            nome TEXT NOT NULL,
            cpf TEXT UNIQUE,
            data_nascimento TEXT,
            tel  TEXT,
            endereco TEXT,
            obs TEXT,
            status TEXT,

            FOREIGN KEY(id)
                REFERENCES usuarios(id)
        )
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

            FOREIGN KEY(cuidador_id) 
                REFERENCES cuidadores(id),

            FOREIGN KEY(paciente_id) 
                REFERENCES pacientes(id),

            UNIQUE(cuidador_id, paciente_id)
        )
    """)

    print("Tabela cuidadores_pacientes criada com sucesso")

    conexao.commit()
    cursor.close()
    conexao.close()

tabela_usuarios()
tabela_paciente()
tabela_cuidadores()
cuidadores_pacientes()