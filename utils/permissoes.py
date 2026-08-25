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

            #VERIFICA A ROLE DO USUARIO LOGADO
            cursor.execute("""
                SELECT role
                FROM usuarios
                WHERE id=?
            """, (usuario_id,))

            usuario = cursor.fetchone()

            conexao.close()

            #VERIFICA SE O USUÁRIO EXISTE
            if not usuario:
                 return jsonify({
                     "erro": "Usuário não encontrado."
                 }), 404

            #VERIFICA SE O USUÁRIO E ADMIN
            if usuario["role"].lower() != "admin":
                return jsonify({
                    "erro": "Apenas ADMIN pode acessar"
                }), 403

            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator

# Recebe as roles permitidas na rota
# Exemplo: @roles_required("admin", "cuidador")
def roles_required(*roles_permitidas):

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            usuario_id = get_jwt_identity()

            conexao = connect()
            cursor = conexao.cursor()

            #BUSCA A ROLE DO USUARIO LOGADO
            cursor.execute("""
                SELECT role
                FROM usuarios
                WHERE id =?
            """,(usuario_id,))

            usuario = cursor.fetchone()

            conexao.close()

            #VERIFICA E O USUÁRIO EXISTE 
            if not usuario:
                return jsonify({
                    "erro": "Usuário não encontrado."
                }), 404

            #VERIFICA SE A ROLE ESTÁ ENTRE AS PERMITIDAS
            if usuario["role"].lower() not in roles_permitidas:
                return jsonify({
                    "erro": "Usuário sem permissão para acessar."
                }), 403

            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator