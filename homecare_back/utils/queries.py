# BUSCA UM USUÁRIO PELO ID
def get_user_by_id(cursor, user_id):
    cursor.execute("""
        SELECT id, name, role, active
        FROM users
        WHERE id = %s
    """, (user_id,))

    return cursor.fetchone()

# BUSCA O VÍNCULO ENTRE UM CUIDADOR E UM PACIENTE
def get_caregiver_patient_link(cursor, caregiver_id, patient_id):
    cursor.execute("""
        SELECT id, active
        FROM caregiver_patient_links
        WHERE caregiver_id = %s
        AND patient_id = %s
    """,(
        caregiver_id,
        patient_id
    ))

    return cursor.fetchone()

# VALIDA SE O USUÁRIO EXISTE E POSSUI A ROLE ESPERADA
def validate_user_role(cursor, user_id, expected_role):
    user = get_user_by_id(cursor, user_id)

    role_name = expected_role.capitalize()

    if not user:
        return None, "nao_encontrado", role_name

    if user["role"].lower() != expected_role.lower():
        return user, "role_invalida", role_name

    return user, None, role_name

# BUSCA UM USUÁRIO PELO E-MAIL
def get_user_by_email(cursor, email):
    cursor.execute("""
            SELECT
                id,
                name,
                email,
                password_hash,
                role,
                active
            FROM users
            WHERE email = %s
    """, (email,))

    return cursor.fetchone()

# BUSCA TODOS OS USUÁRIOS
def get_all_users(cursor):
    cursor.execute("""
        SELECT 
            id,
            name,
            email,
            role,
            active
        FROM users
        ORDER BY id
    """)

    return cursor.fetchall()

# BUSCA OUTRO USUÁRIO COM O MESMO E-MAIL, IGNORANDO O PRÓPRIO ID
def get_user_by_email_except_id(cursor, email, user_id):
    cursor.execute("""
        SELECT id
        FROM users
        WHERE email = %s
        AND id != %s
    """, (
        email,
        user_id
    ))

    return cursor.fetchone()

# CRIA UMA NOVA CONTA E RETORNA O ID DO USUÁRIO
def create_account(cursor, name, email, password_hash, role, cpf, birth_date, phone, address):
    cursor.execute("""
        INSERT INTO users (
            name,
            email,
            password_hash,
            role,
            cpf,
            birth_date,
            phone,
            address
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        name,
        email,
        password_hash,
        role,
        cpf,
        birth_date,
        phone,
        address
    ))

    return cursor.fetchone()["id"]

# CRIA O PERFIL DE PACIENTE PARA UM USUÁRIO
def create_patient(cursor, user_id):
    cursor.execute("""
        INSERT INTO patients (user_id)
        VALUES (%s)
    """, (user_id,))

# CRIA O PERFIL DE CUIDADOR PARA UM USUÁRIO
def create_caregiver(cursor, user_id):
    cursor.execute("""
        INSERT INTO caregivers (user_id)
        VALUES (%s)
    """, (user_id,))

# BUSCA O HASH DA SENHA DE UM USUÁRIO PELO ID
def get_user_password_by_id(cursor, user_id):
    cursor.execute("""
        SELECT id, password_hash
        FROM users
        WHERE id = %s
    """, (user_id,))

    return cursor.fetchone()

# ATUALIZA A SENHA DE UM USUÁRIO
def update_user_password(cursor, user_id, password_hash):
    cursor.execute("""
        UPDATE users
        SET password_hash = %s
        WHERE id = %s
    """, (
        password_hash,
        user_id
    ))

# BUSCA TODOS OS USUÁRIOS COM ROLE DE PACIENTE
def get_patient_data(cursor):
    cursor.execute("""
        SELECT 
            id,
            name,
            cpf,
            birth_date,
            phone,
            address,
            active
        FROM users
        WHERE role = 'patient'
        ORDER BY id
    """)

    return cursor.fetchall()

# BUSCA OS DADOS DE UM PACIENTE PELO ID
def get_patient_data_by_id(cursor, user_id):
    cursor.execute("""
            SELECT 
                id,
                name,
                cpf,
                birth_date,
                phone,
                address,
                active
            FROM users
            WHERE role = 'patient'
            AND id = %s
        """, (user_id,))
    
    return cursor.fetchone()

# BUSCA TODOS OS USUÁRIOS COM ROLE DE CUIDADOR
def get_caregiver_data(cursor):
    cursor.execute("""
            SELECT 
                id,
                name,
                cpf,
                birth_date,
                phone,
                address,
                active
            FROM users
            WHERE role = 'caregiver'
        """)
    
    return cursor.fetchall()

# BUSCA OS DADOS DE UM CUIDADOR PELO ID
def get_caregiver_data_by_id(cursor, user_id):
    cursor.execute("""
            SELECT 
                id,
                name,
                cpf,
                birth_date,
                phone,
                address,
                active
            FROM users
            WHERE role = 'caregiver'
            AND id = %s
        """, (user_id,))

    return cursor.fetchone()

# BUSCA OUTRO USUÁRIO COM O MESMO CPF, IGNORANDO O PRÓPRIO ID
def get_user_cpf_except_id(cursor, cpf, user_id):
    cursor.execute("""
                SELECT id
                FROM users
                WHERE cpf = %s
                AND id != %s
            """, (
                cpf,
                user_id
            ))

    return cursor.fetchone()

# ATUALIZA DINAMICAMENTE OS CAMPOS DE UM USUÁRIO
def update_user_fields(cursor, user_id, fields, values):

    params = values + [user_id]

    cursor.execute(f"""
            UPDATE users
            SET {", ".join(fields)}
            WHERE id = %s
        """, params)

# DESATIVA UM USUÁRIO
def disable_user(cursor, user_id):
    cursor.execute("""
        UPDATE users
        SET active = false
        WHERE id = %s
    """, (user_id,))

# CRIA UM VÍNCULO ENTRE CUIDADOR E PACIENTE
def generate_link(cursor, caregiver_id, patient_id):
    cursor.execute("""
        INSERT INTO caregiver_patient_links(
                caregiver_id,
                patient_id,
                created_date,
                created_time
            )
        VALUES (%s, %s, CURRENT_DATE, CURRENT_TIME)
         RETURNING id
    """, (
        caregiver_id,
        patient_id
    ))

    return cursor.fetchone()["id"]

# DESATIVA O VÍNCULO ENTRE CUIDADOR E PACIENTE
def disable_link(cursor, caregiver_id, patient_id):
    cursor.execute("""
        UPDATE caregiver_patient_links
        SET active = false
        WHERE caregiver_id = %s
        AND patient_id = %s
    """,(
        caregiver_id,
        patient_id
    ))

# BUSCA OS PACIENTES ATIVOS VINCULADOS A UM CUIDADOR
def get_patients_by_caregiver(cursor, caregiver_id):
    cursor.execute("""
        SELECT
            u.id,
            u.name,
            u.cpf,
            u.birth_date,
            u.phone,
            u.address,
            u.active
        FROM caregiver_patient_links cpl
        JOIN users u
            ON cpl.patient_id = u.id
        WHERE cpl.caregiver_id = %s
        AND cpl.active = true
    """, (caregiver_id,))

    return cursor.fetchall()

# BUSCA OS CUIDADORES ATIVOS VINCULADOS A UM PACIENTE
def get_caregivers_by_patient(cursor, patient_id):
    cursor.execute("""
        SELECT
            u.id,
            u.name,
            u.cpf,
            u.birth_date,
            u.phone,
            u.address,
            u.active
        FROM caregiver_patient_links cpl
        JOIN users u
            ON cpl.caregiver_id = u.id
        WHERE cpl.patient_id = %s
        AND cpl.active = true
    """, (patient_id,))

    return cursor.fetchall()

# CRIA UM NOVO PERÍODO NO HISTÓRICO DE UM VÍNCULO
def create_link_history(cursor, link_id):
    cursor.execute("""
        INSERT INTO caregiver_patient_link_history(
            link_id,
            started_date,
            started_time
            )
        VALUES (%s, CURRENT_DATE, CURRENT_TIME)
         RETURNING id
    """, (link_id,))

    return cursor.fetchone()["id"]

# FINALIZA O PERÍODO ATIVO NO HISTÓRICO DE UM VÍNCULO
def close_link_history(cursor, link_id):
    cursor.execute("""
        UPDATE caregiver_patient_link_history
        SET
            ended_date = CURRENT_DATE,
            ended_time = CURRENT_TIME
        WHERE link_id = %s
        AND ended_date IS NULL
        AND ended_time IS NULL
    """, (link_id,))
