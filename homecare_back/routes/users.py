import psycopg
from flask import jsonify, request, Blueprint
from database.connect import connect
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.permissions import roles_required
from werkzeug.security import generate_password_hash, check_password_hash
from services.account_service import process_account_creation

from utils.response import validate_non_empty_fields, validate_required_fields
from utils.queries import (
    get_all_users,
    get_user_by_id,
    get_user_by_email_except_id,
    get_user_by_email,
    get_user_password_by_id,
    update_user_password
)

import sqlite3

user_bp = Blueprint("users", __name__, url_prefix="/users")

# CONSULTAR USUARIO (TODOS)
@user_bp.route("", methods=['GET'])
@jwt_required()
@roles_required("admin")
def list_users():
    connection = None
    try:
        connection = connect()
        cursor = connection.cursor()

        #BUSCANDO TODOS OS USUARIOS NO BANCO
        users = get_all_users(cursor)

        result = [dict(user) for user in users]

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

    finally: 
        if connection:
            connection.close()


# CONSULTAR USUARIO POR (ID)
@user_bp.route("/<int:user_id>", methods=['GET'])
@jwt_required()
@roles_required("admin")
def get_user(user_id):
    connection = None

    try:
        connection = connect()
        cursor = connection.cursor()

        user = get_user_by_id(cursor, user_id)

        if not user:
            return jsonify({
                "error": "Usuário não encontrado."
            }), 404

        return jsonify(dict(user)), 200

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

    finally:
        if connection:
            connection.close()

# EDITAR USUARIO PARCIAL (ID)
@user_bp.route("/<int:user_id>", methods=['PATCH'])
@jwt_required()
@roles_required("admin")
def update_user(user_id):
    connection = None

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "error": "Dados não enviados"
            }), 400
        
        connection = connect()
        cursor = connection.cursor()

        #BUSCA O USUÁRIO E A ROLE NO BANCO DE DADOS
        user = get_user_by_id(cursor, user_id)  

        if not user:
            return jsonify({
                "error": "Usuário não encontrado."
            }), 404

        # CAMPOS QUE PODEM SER ALTERADOS
        allowed_fields = ["name", "email", "password"]

        for field in data:
            if field not in allowed_fields:
                return jsonify({
                    "error": f"Campo '{field.upper()}' não pode ser alterado."
                }), 400

        error = validate_non_empty_fields(data, allowed_fields)

        if error:
            return jsonify({
                "error": error
            }), 400
        
        fields = []
        values = []

        for field in allowed_fields:
            if field in data:
                value = data[field]

                if field == "password":
                    value = generate_password_hash(value)
                    db_field = "password_hash"
                else:
                    db_field = field

                fields.append(f"{db_field} = %s")
                values.append(value)

        if not fields:
             return jsonify({
                 "error": "Nenhum campo válido foi enviado para edição."
             }), 400

        #VERIFICA DUPLICIDADE NO EMAIL ALTERADO
        if "email" in data:
            existing_email = get_user_by_email_except_id(
                cursor,
                data["email"],
                user_id
            )

        if existing_email:
            return jsonify({
                "error": "Email já utilizado por outro usuário."
            }), 400

        values.append(user_id)

        sql = f"""
            UPDATE users 
            SET {', '.join(fields)}
            WHERE id = %s
        """
        cursor.execute(sql, values)

        connection.commit()

        return_data = {
            field: value
            for field, value in data.items()
            if field != "password"
        }

        return jsonify ({
            "message": "Usuário atualizado com sucesso.",
            "user": user_id,
            "edited_data": return_data
        }), 200

    except psycopg.IntegrityError as e:
        if connection:
            connection.rollback()

        return jsonify({
            "error": str(e)
        }), 400

    except Exception as e:
        if connection:
            connection.rollback()

        return jsonify({
            "error": str(e)
        }), 500

    finally:
        if connection:
            connection.close()

#DESATIVAR USUARIO
@user_bp.route("/<int:user_id>", methods=['DELETE'])
@jwt_required()
@roles_required("admin")
def disable_user(user_id):
    connection = None

    try:
        connection = connect()
        cursor = connection.cursor()

        #BUSCA O USUARIO E A ROLE E STATUS
        cursor.execute("""
            SELECT 
                u.role,
                p.status AS paciente_status,
                c.status AS cuidador_status 
            FROM users u

            LEFT JOIN pacientes p 
                ON p.id = u.id

            LEFT JOIN cuidadores c  
                ON c.id = u.id
            WHERE u.id =?
        """, (user_id,))

        user = cursor.fetchone()

        if not user:
             return jsonify({
                 "erro": "Usuário não encontrado."
             }), 404
        
        role = user["role"].lower()

        #PEGA STATUS DE ACORDO COM A ROLE
        if role == "paciente":
            status = user["paciente_status"]

        elif role == "cuidador":
            status = user["cuidador_status"]


        #SE FOR ADMIN NAO DESATIVA
        else:
            return jsonify({
                "erro": "Este tipo de usuário não pode ser desativado por esta rota."
            }), 400
        
        if status is None:
            return jsonify({
                "erro": "Cadastro especifíco do usuário não encontrado."
            }), 404
        
        #VERIFICA SE JA ESTA INATIVO
        if status == "inativo":
            return jsonify({
                "erro": "Usuário já está inativo."
            }), 400

        #DESATIVAR PACIENTE
        if role == "paciente":
            cursor.execute("""
                UPDATE pacientes
                SET status = 'inativo'
                WHERE id = ?
            """, (user_id,))

        #DESATIVAR CUIDADOR
        elif role == "cuidador":
            cursor.execute("""
                UPDATE cuidadores
                SET status = 'inativo'
                WHERE id = ?
            """, (user_id,))
        
        connection.commit()

        return jsonify({
            "msg": "Usuário desativado com sucesso.",
            "user_id": user_id,
            "role": role,
            "status": 'inativo'
        }), 200

    except sqlite3.IntegrityError as e:
        if connection:
            connection.rollback()

        return jsonify({
            "erro": str(e)
        }), 400

    except Exception as e:
        if connection: 
            connection.rollback()

        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if connection:
            connection.close()

# CRIAR USUARIO PUBLICO
@user_bp.route("", methods=['POST'])
def register():
    new_user = request.get_json()

    user_id, error, status = process_account_creation(new_user,["patient", "caregiver"])

    if error:
        return jsonify({
            "error": error, 
        }), status

    return jsonify({
        "message": "Conta criada com sucesso.",
        "id": user_id
    }), status

# CRIAR USUARIO ADMIN
@user_bp.route("", methods=['POST'])
@jwt_required()
def create_user():
    new_user = request.get_json()

    user_id, error, status = process_account_creation(new_user,["admin", "patient", "caregiver"])

    if error:
        return jsonify({
            "error": error, 
        }), status

    return jsonify({
        "message": "Conta criada com sucesso.",
        "id": user_id
    }), status

#ROTA ESQUECI SENHA
@user_bp.route("/forgot-password", methods=['POST'])
def forgot_password():
    data = request.get_json()

    if not data or not data.get("email", "").strip():
        return jsonify({
            "error": "E-mail é obrigatório"
        }), 400

    email = data["email"].strip().lower()

    connection= None

    try:
        connection = connect()
        cursor = connection.cursor()

        user_email = get_user_by_email(cursor, email)

        if not user_email:
            return jsonify({
                "error": "E-mail não encontrado"
            }), 404

        return jsonify({
            "message": "E-mail encontrado"
        }), 200
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

    finally:
        if connection:
            connection.close()

#ALTERAR SENHA
@user_bp.route("change-password", methods=['PATCH'])
@jwt_required()
def change_password():
    connection = None

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "error": "Dados não encontrados."
            }), 400

        required_fields = [
            "password",
            "new_password",
            "confirm_password"
        ]

        error = validate_required_fields(data, required_fields)

        if error:
            return jsonify({
                "error": error
            }), 400

        #VERIFICA SE AS SENHAS SÃO IGUAIS
        if data["new_password"] != data["confirm_password"]:
            return jsonify({
                "error": "As senhas não coincidem."
            }), 400
        
        user_id = int(get_jwt_identity())

        connection = connect()
        cursor = connection.cursor()

        #BUSCA USUARIO E A SENHA ATUAL
        user = get_user_password_by_id(cursor, user_id)

        if not user:
            return jsonify({
                "error": "Usuário não encontrado."
            }), 404

        #CONFERE SENHA ATUAL
        if not check_password_hash(
            user["password_hash"],
            data["password"]
        ):
            return jsonify({
                "error": "Senha atual incorreta."
            }), 400

        #EVITAR DUPLICIDADE DE SENHA
        if check_password_hash (
            user["password_hash"],
            data["new_password"]
        ):
            return jsonify({
                "error": "A nova senha não pode ser igual à senha atual."
            }), 400

        #GERA O HASH DA NOVA SENHA
        new_password_hash = generate_password_hash(data["new_password"])

        update_user_password(cursor, user_id, new_password_hash)

        connection.commit()
        
        return jsonify({
            "message": "Senha alterada com sucesso."
        }), 200

    except Exception as e:
        if connection:
            connection.rollback()

        return jsonify({
            "error": str(e)
        }), 500

    finally:
        if connection:
            connection.close()
