from flask_jwt_extended import get_jwt_identity
from flask import jsonify
from database.connect import connect
from functools import wraps

def admin_required():
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            usuario_id = get_jwt_identity()

            conexao = connect()
            cursor = conexao.cursor()

            cursor.execute("""
                SELECT role
                FROM usuarios
                WHERE id=?
            """, (usuario_id,))

            usuario = cursor.fetchone()

            conexao.close()

            if not usuario or usuario["role"] != "ADMIN":
                return jsonify({
                    "erro": "Apenas ADMIN pode acessar"
                }), 403

            return func(*args, **kwargs)
        return wrapper
    return decorator