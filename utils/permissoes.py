from flask_jwt_extended import get_jwt_identity
from database.connect import connect

def verificar_admin():
    usuario_id = get_jwt_identity()

    conexao = connect()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT role FROM usuarios
        WHERE id=?
    """, (usuario_id),)

    usuario = cursor.fetchone()

    conexao.close()

    if usuario and usuario["role"] == "ADMIN":
        return True
    return False
