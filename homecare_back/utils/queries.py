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
        SELECT id, active
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
    
    return cursor.fetchall()

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
    
    return cursor.fetchone()

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

    return cursor.fetchall()

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

def update_user_fields(cursor, user_id, fields, values):

    params = values + [user_id]

    cursor.execute(f"""
            UPDATE users
            SET {", ".join(fields)}
            WHERE id = %s
        """, params)

    return cursor.fetchone()

def disable_user(cursor, user_id):
    cursor.execute("""
        UPDATE users
        SET active = false
        WHERE id = %s
    """, (user_id,))

def generate_link(cursor, caregiver_id, patient_id):

    cursor.execute("""
        INSERT INTO caregiver_patient_links
            caregiver_id,
            patient_id,
            created_date,
            created_time
        VALUE (%s, %s, CURRENT_DATE, CURRENT_TIME)
    """, (
        caregiver_id,
        patient_id
    ))

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

def create_link_history(cursor, link_id):
    cursor.execute("""
        INSERT INTO caregiver_patient_link_history(
            link_id,
            started_data,
            started_time
            )
        VALUES (%s, CURRENT_DATE, CURRENT_TIME)
         RETURNING id
    """, (link_id,))

    return cursor.fetchone()["id"]

def close_link_history(cursor, link_id):
    cursor.executer("""
        UPDATE caregiver_patient_link_history
        SET
            ended_date = CURRENT_DATE,
            ended_time = CURRENT_TIME
        WHERE link_id = %s
        AND ended_date IS NULL
        AND ended_time IS NULL
    """, (link_id,))
