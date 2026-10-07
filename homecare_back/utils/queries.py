#BUSCAR USUARIO VIA ID
def get_user_by_id(cursor, user_id):
    cursor.execute("""
        SELECT id, name, role, active
        FROM users
        WHERE id = %s
    """, (user_id,))

    return cursor.fetchone()

#CONSULTA VINCULDO DO CUIDADOR COM PACIENTE
def get_caregiver_patient_link(cursor, caregiver_id, patient_id):
    cursor.execute("""
        SELECT id
        FROM caregiver_patient_links
        WHERE caregiver_id = %s
        AND patient_id = %s
    """,(
        caregiver_id,
        patient_id
    ))

    return cursor.fetchone()

#VERIFICA A ROLE 
def validate_user_role(cursor, user_id, expected_role):
    user = get_user_by_id(cursor, user_id)

    role_name = expected_role.capitalize()

    if not user:
        return None, "nao_encontrado", role_name

    if user["role"].lower() != expected_role.lower():
        return user, "role_invalida", role_name

    return user, None, role_name


# BUSCA USUARIO PELO EMAIL
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

#BUSCA TODOS OS USUARIOS
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

#INSERE USUARIO NO BANCO
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

#INSERE O PACIENTE
def create_patient(cursor, user_id):
    cursor.execute("""
        INSERT INTO patients (user_id)
        VALUES %s
    """, (user_id,))
    
def create_caregiver(cursor, user_id):
    cursor.execute("""
        INSERT INTO caregivers (user_id)
        VALUES %s
    """, (user_id,))

def get_user_password_by_id(cursor, user_id):
    cursor.execute("""
        SELECT id, password_hash
        FROM users
        WHERE id = %s
    """, (user_id,))

    return cursor.fetchone()

def update_user_password(cursor, user_id, password_hash):
    cursor.execute("""
        UPDATE users
        SET password_hash = %s
        WHERE id = %s
    """, (
        password_hash,
        user_id
    ))