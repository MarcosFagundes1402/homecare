import psycopg
from flask import jsonify, request, Blueprint
from database.connect import connect
from flask_jwt_extended import jwt_required
from utils.permissions import roles_required
from utils.response import error_role, validate_non_empty_fields
from utils.queries import (
    validate_user_role,
    get_caregiver_data,
    get_caregiver_data_by_id,
    get_user_cpf_except_id,
    update_user_fields,
    disable_user
    )

caregiver_bp = Blueprint("caregivers", __name__, url_prefix="/caregivers")

#CONSULTAR TODOS OS CUIDADORES
@caregiver_bp.route("", methods=['GET'])
@jwt_required()
@roles_required("admin")
def list_caregivers():
    connection = None

    try:
        connection = connect()
        cursor = connection.cursor()

        caregivers = get_caregiver_data(cursor)
    
        caregiver_list = [dict(caregiver) for caregiver in caregivers]

        return jsonify(caregiver_list), 200

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500
    
    finally:
        if connection:
            connection.close()

#CONSULTANDO CUIDADORES POR ID
@caregiver_bp.route("/<int:user_id>", methods=['GET'])
@jwt_required()
@roles_required("admin")
def list_caregiver_by_id(user_id):
    connection = None

    try:
        connection = connect()
        cursor = connection.cursor()

        #VALIDA SE O ID PERTENCE A UM CUIDADOR
        caregiver, error, role_name = validate_user_role(cursor, user_id, "caregiver")

        if error:
            return error_role(error, role_name, caregiver)

        #BUSCAR OS DADOS NO CUIDADOR
        caregiver_data = get_caregiver_data_by_id(cursor, user_id)

        if not caregiver_data:
            return jsonify({
                "error": "Cuidador não encontrado."
            }), 404

        return jsonify({
            "caregiver": dict(caregiver_data)
        }), 200

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

    finally:
        if connection:
            connection.close()

#EDITAR CUIDADOR 
@caregiver_bp.route("/<int:id>", methods=['PATCH'])
@jwt_required()
@roles_required("admin")
def edit_caregiver(user_id):
    connection = None

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "error": "Dados não encontrados."
            }), 400

        connection = connect()
        cursor = connection.cursor()

        #VALIDA SE O ID PERTENCE A UM CUIDADOR
        caregiver, error, role_name = validate_user_role(cursor, user_id, "caregiver")

        if error:
            return error_role(error, role_name, caregiver)

        #CAMPOS QUE PODEM SER EDITADOS
        allowed_fields = [
            "cpf",
            "birth_date",
            "phone",
            "address",
        ]

        #VALIDA O CAMPO NAO PERMITIDOS
        for field in data:
            if field not in allowed_fields:
                return jsonify({
                    "error": f"O campo '{field}' não pode ser editado."
                }), 400

        non_empty_fields = [
            "cpf",
            "birth_date",
            "phone",
            "address",
        ]

        error = validate_non_empty_fields(data, non_empty_fields)

        if error:
            return jsonify({
                "error": error
            }), 400

        #VERIFICA CPF DUPLICADO
        if "cpf" in data:
            existing_cpf = get_user_cpf_except_id(cursor, data["cpf"], user_id)

            if existing_cpf:
                return jsonify({
                    "error": "CPF já cadastrado."
                }), 400

        #MONTA UPDATE DINAMICO
        fields = []
        values = []

        for field in allowed_fields:
            if field in data:
                fields.append(f"{field} = %s")
                values.append(data[field])

        if not fields:
            return jsonify({
                "error": "Nenhum campo válido foi enviado para edição."
            }), 400

        #ATUALIZAR CUIDADOR
        update_user_fields(cursor, user_id, fields, values)

        connection.commit()

        return jsonify({
            "message": "Cuidador atualizado com sucesso.",
            "caregiver_id": user_id,
            "updated_fields": data
        }), 200

    except psycopg.IntegrityError:
        if connection:
            connection.rollback()

        return jsonify({
            "error": "CPF já cadastrado."
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

#DESATIVAR CUIDADOR
@caregiver_bp.route("/<int:id>", methods=['DELETE'])
@jwt_required()
@roles_required("admin")
def disable_caregiver(user_id):
    connection = None

    try:
        connection = connect()
        cursor = connection.cursor()

        #VALIDA SE O ID PERTENCE A UM CUIDADOR
        caregiver, error, role_name = validate_user_role(cursor, user_id, "caregiver")

        if error:
            return error_role(error, role_name, caregiver)


        if not caregiver["active"]:
            return jsonify({
                "error": "Cuidador já está inativo."
            }), 400

        #DESATIVA CUIDADOR
        disable_user(cursor, user_id)

        connection.commit()

        return jsonify({
            "message": "Cuidador desativado com sucesso.",

            "caregiver": {
                "id": caregiver["id"],
                "name": caregiver["name"],
                "active": False
            }
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