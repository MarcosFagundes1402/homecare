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

def tabela_cuidadores_pacientes():

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

def tabela_medicamentos():
    conexao = connect()
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicamentos(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTERGER NOT NULL,
            nome TEXT NOT NULL,
            dosagem TEXT,
            horario TEXT,
            obs TEXT,
            status TEXT DEFAULT 'ativo',
            FOREIGN KEY (paciente_id) REFERENCES pacientes(id))
    """)

    print("Tabela de medicamentos criado com sucesso.")
    
    conexao.commit()
    conexao.close()

def tabela_administracao_medicamentos():
    conexao = connect()
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS administracao_medicamentos(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medicamento_id INTEGER NOT NULL,
            paciente_id INTEGER NOT NULL,
            responsavel_id INTEGER NOT NULL,
            horario_previsto TEXT,
            horario_administrado TEXT,
            dosagem_administrada TEXT NOT NULL,
            status TEXT NOT NULL,
            obs TEXT,

            FOREIGN KEY (medicamento_id) REFERENCES medicamentos(id),
            FOREIGN KEY (paciente_id) REFERENCES pacientes(id),
            FOREIGN KEY (responsavel_id) REFERENCES usuarios(id)
        )
    """)

    print("Tabela administração e medicamentos criado com sucesso.")

    conexao.commit()
    conexao.close()

def tabela_relatorios_diarios():
    conexao = connect()
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS relatorios_diarios(
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            paciente_id INTEGER NOT NULL,
            responsavel_id INTEGER NOT NULL,

            alimentacao TEXT,
            higiene TEXT,

            pressao_arterial TEXT,
            glicemia TEXT,
            temperatura TEXT,

            observacoes TEXT,

            data_horario TEXT NOT NULL,

            FOREIGN KEY (paciente_id) REFERENCES pacientes(id),
            FOREIGN KEY (responsavel_id) REFERENCES usuarios(id)
        )
    """)

    print("Tabela de relatorio criada com sucesso!")

    conexao.commit()
    conexao.close()



tabela_usuarios()
tabela_paciente()
tabela_cuidadores()
tabela_cuidadores_pacientes()
tabela_medicamentos()
tabela_administracao_medicamentos()
tabela_relatorios_diarios()