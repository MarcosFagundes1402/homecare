from flask_jwt_extended import get_jwt_identity
from flask import jsonify
from database.connect import connect
from functools import wraps
from utils.queries import get_user_by_id

# Recebe as roles permitidas na rota
# Exemplo: @roles_required("admin", "cuidador")
def roles_required(*allowed_roles):
    allowed_roles = tuple(role.lower() for role in allowed_roles)
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            
            user_id = int(get_jwt_identity())

            connection = None

            try:
                connection = connect()
                cursor = connection.cursor()

                #BUSCA A ROLE DO USUARIO LOGADO
                user = get_user_by_id(cursor, user_id)

                #VERIFICA SE O USUÁRIO EXISTE 
                if not user:
                    return jsonify({
                        "erro": "Usuário não encontrado."
                    }), 404

                #VERIFICA SE A ROLE ESTÁ ENTRE AS PERMITIDAS
                if user["role"].lower() not in allowed_roles:
                    return jsonify({
                        "erro": "Usuário sem permissão para acessar."
                    }), 403

                return func(*args, **kwargs)

            finally:
                if connection:
                    connection.close()
        
        return wrapper
    
    return decorator