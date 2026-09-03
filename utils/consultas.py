#BUSCAR USUARIO VIA ID
def buscar_usuario_por_id(cursor, usuario_id):
    cursor.execute("""
        SELECT id, nome, role
        FROM usuarios
        WHERE id = ?
    """, (usuario_id,))

    return cursor.fetchone()

#BUSCAR STATUS DO CUIDADOR
def cuidador_status(cursor, usuario_id):
    cursor.execute("""
        SELECT id, status
        FROM cuidadores
        WHERE id = ?
    """, (usuario_id,))

    return cursor.fetchone()

#BUSCAR STATUS DO PACIENTE
def paciente_status(cursor, usuario_id):
    cursor.execute("""
        SELECT id, status
        FROM pacientes
        WHERE id = ?
    """, (usuario_id,))

    return cursor.fetchone()

#CONSULTA VINCULDO DO CUIDADOR COM PACIENTE
def vinculo_cp(cursor, cuidador_id, paciente_id):
    cursor.execute("""
        SELECT id
        FROM cuidadores_pacientes
        WHERE cuidador_id = ?
        AND paciente_id = ?
    """,(
        cuidador_id,
        paciente_id
    ))

    return cursor.fetchone()

#VERIFICA A ROLE 
def buscar_role(cursor, usuario_id, role_esperada):
    usuario = buscar_usuario_por_id(cursor, usuario_id)

    role_nome = role_esperada.capitalize()

    if not usuario:
        return None, "nao_encontrado", role_nome

    if usuario["role"].lower() != role_esperada.lower():
        return usuario, "role_invalida", role_nome

    return usuario, None, role_nome
