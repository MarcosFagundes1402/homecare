from flask_jwt_extended import get_jwt_identity
from flask import jsonify
from database.connect import connect
from functools import wraps
from utils.consultas import buscar_usuario_por_id

# Recebe as roles permitidas na rota
# Exemplo: @roles_required("admin", "cuidador")
def roles_required(*roles_permitidas):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            
            usuario_id = get_jwt_identity()

            conexao = None

            try:
                conexao = connect()
                cursor = conexao.cursor()

                #BUSCA A ROLE DO USUARIO LOGADO
                usuario = buscar_usuario_por_id(cursor, usuario_id)

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

            finally:
                if conexao:
                    conexao.close()
        
        return wrapper
    
    return decorator