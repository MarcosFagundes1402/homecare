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
