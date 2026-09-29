#BUSCAR USUARIO VIA ID
def get_user_by_id(cursor, user_id):
    cursor.execute("""
        SELECT id, nome, role
        FROM usuarios
        WHERE id = ?
    """, (user_id,))

    return cursor.fetchone()

#BUSCAR STATUS DO CUIDADOR
def caregiver_stats(cursor, user_id):
    cursor.execute("""
        SELECT id, status
        FROM cuidadores
        WHERE id = ?
    """, (user_id,))

    return cursor.fetchone()

#BUSCAR STATUS DO PACIENTE
def patient_stats(cursor, user_id):
    cursor.execute("""
        SELECT id, status
        FROM pacientes
        WHERE id = ?
    """, (user_id,))

    return cursor.fetchone()

#CONSULTA VINCULDO DO CUIDADOR COM PACIENTE
def get_caregiver_patient_link(cursor, caregiver_id, patient_id):
    cursor.execute("""
        SELECT id
        FROM cuidadores_pacientes
        WHERE cuidador_id = ?
        AND paciente_id = ?
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
