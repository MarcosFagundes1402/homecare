import psycopg
from flask import jsonify, request, Blueprint
from database.connect import connect
from flask_jwt_extended import jwt_required
from utils.permissions import roles_required
from utils.response import validate_non_empty_fields, error_role

from utils import (
    validate_user_role,
    error_role,
    )

from utils.queries import (
    get_patient_data,
    get_patient_data_by_id,
    get_user_cpf_except_id,
    update_user_fields,
    disable_user
)

patient_bp = Blueprint("patient", __name__, url_prefix="/patient")

# CONSULTADO TODOS PACIENTES
@patient_bp.route("", methods=['GET'])
@jwt_required()
@roles_required("admin")
def list_patients():

    connection = None

    try: 
        connection = connect()
        cursor = connection.cursor()

        patients = get_patient_data(cursor)

        patients_list = [dict(patient) for patient in patients]

        return jsonify (patients_list), 200

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

    finally:
        if connection:
            connection.close()

#CONSULTANDO PACIENTES POR ID
@patient_bp.route("/<int:user_id>", methods=['GET'])
@jwt_required()
@roles_required("admin")
def get_patient_by_id(user_id):
    connection = None

    try:
        connection = connect()
        cursor = connection.cursor()

        #VALIDA SE O ID PERTENCE A UM PACIENTE
        patient, error, role_name = validate_user_role(cursor, user_id, "patient")

        if error:
            return error_role(error, role_name, patient)

        #BUSCA OS DADOS DO PACIENTE
        patient_data = get_patient_data_by_id(cursor, user_id)

        if not patient_data:
            return jsonify({
                "error": "Paciente não encontrado."
            }), 404

        return jsonify({
            "patient": dict(patient_data)
        }), 200

    except Exception as e:
        return jsonify ({
            "error": str(e)
        }), 500

    finally:
        if connection:
            connection.close()

#EDITAR PACIENTE
@patient_bp.route("/<int:user_id>", methods=['PATCH'])
@jwt_required()
@roles_required("admin")
def edit_patient(user_id):

    connection = None

    try: 
        data = request.get_json()

        if not data:
            return jsonify({
                "error": "Dados não encontrados."
            }), 400

        
        connection = connect()
        cursor = connection.cursor()

        #VALIDA SE O ID PERTENCE A UM PACIENTE
        patient, error, role_name = validate_user_role(cursor, user_id, "patient")

        if error:
            return error_role(error, role_name, patient)

        #CAMPOS QUE PODEM SER EDITADOS
        allowed_fields = [
            "cpf",
            "birth_date",
            "phone",
            "address"
        ]

        for field in data:
            if field not in allowed_fields:
                return jsonify({
                    "erro": f"O campo '{field}' não pode ser editado."
                }), 400

        #CAMPOS QUE NÃO PODEM FICAR VAZIOS
        non_empty_fields = [
            "cpf",
            "birth_date",
            "phone",
            "address"
        ]

        error = validate_non_empty_fields(data, non_empty_fields)

        if error:
            return jsonify({
                "error": error
            }), 400

        #SE O CPF ENVIADO, VERIFICA DUPLICIDADE
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


        #ATUALIZA PACIENTE
        update_user_fields(cursor, user_id, fields, values)

        connection.commit()

        return jsonify({
            "message": "Paciente atualizado com sucesso.",
            "patient_id": user_id,
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

# DESATIVAR PACIENTE 
@patient_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
@roles_required("admin")
def disable_patient(user_id):

    connection = None

    try:
        connection = connect()
        cursor = connection.cursor()

        patient, error, role_name = validate_user_role(cursor, user_id, "patient")

        if error:
            return error_role(error, role_name, patient)

        if not patient["active"]:
            return jsonify({
                "error": "Paciente já está inativo."
            }), 400

        #DESATIVA USUARIO
        disable_user(cursor, user_id)

        connection.commit()

        return jsonify({
            "message": "Paciente desativado com sucesso.",

            "patient": {
                "id": patient["id"],
                "name": patient["name"],
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