from flask import Blueprint, jsonify, request
from database.connect import connect
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.permissions import roles_required
from utils.response import error_role
from utils.queries import (
        get_caregiver_patient_link,
        validate_user_role,
        generate_link,
        get_patients_by_caregiver,
        get_caregivers_by_patient,
        disable_link
    ) 


caregiver_patient_bp = Blueprint("links", __name__, url_prefix="/links")

# CRIA O VINCULO ENTRE CUIDADOR E PACIENTE
@caregiver_patient_bp.route("", methods=["POST"])
@jwt_required()
@roles_required("admin")
def create_link():

    connection = None

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "error": "Dados não encontrados."
            }), 400

        if "caregiver_id" not in data or "patient_id" not in data:
            return jsonify({
                "error": "OS IDs de cuidador e paciente são obrigatórios."
            }), 400

        connection = connect()
        cursor = connection.cursor()

        # VERIFICA SE O ID INFORMADO COMO CUIDADOR EXISTE
        caregiver, error, role_name = validate_user_role(cursor, data["caregiver_id"], "caregiver")

        # RETORNA ERRO SE O USUARIO NAO EXISTIR OU A ROLE FOR INVALIDA
        if error:
            return error_role(error, role_name, caregiver)

        if not caregiver["active"]:
            return jsonify({
                "error": "Não é possível vincular um cuidador inativo."
            }), 400
        
        # VERIFICA SE O ID INFORMADO COMO PACIENTE EXISTE
        patient, error, role_name = validate_user_role(cursor, data["patient_id"], "patient")

        # RETORNA ERRO SE O USUARIO NAO EXISTIR OU A ROLE FOR INVALIDA
        if error:
            return error_role(error, role_name, patient)

        if not patient["active"]:
            return jsonify({
                "error":"Não é possível vincular um paciente inativo."
            }), 400
        
        # VERIFICA SE O VINCULO JÁ EXISTE
        existing_link = get_caregiver_patient_link(cursor, data["caregiver_id"], data["patient_id"])
 
        if existing_link:
            return jsonify({
                "error": "Este cuidador já está vinculado a este paciente."
            }), 409

        # CRIA O VINCULO
        generate_link(cursor, data["caregiver_id"], data["patient_id"])
      
        connection.commit()

        return jsonify({
            "message": "Vínculo criado com sucesso.",
            "caregiver": {
                "id": caregiver["id"],
                "name": caregiver["name"]
            },
            "patient": {
                "id": patient["id"],
                "name": patient["name"]
            }
        }), 201

    except Exception as e:
        if connection:
            connection.rollback()

        return jsonify({
            "error": str(e)
        }), 500

    finally:
        if connection:
            connection.close()


# MOSTRA OS PACIENTES QUE O CUIDADOR TEM
@caregiver_patient_bp.route("/<int:user_id>", methods=["GET"])
@jwt_required()
@roles_required("admin")
def list_caregiver_patients(user_id):

    connection = None

    try:
        connection = connect()
        cursor = connection.cursor()

        # VERIFICA SE O ID INFORMADO COMO CUIDADOR EXISTE
        caregiver, error, role_name = validate_user_role(cursor, user_id, "caregiver")

        # RETORNA O ERRO SE A ROLE NAO EXISTIR
        if error:
            return error_role(error, role_name, caregiver)

   
        # BUSCA OS PACIENTES VINCULADOS
        patients = get_patients_by_caregiver(cursor, user_id)

        if not patients:
            return jsonify([]), 200

        result = [dict(patient) for patient in patients]

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

    finally:
        if connection:
            connection.close()

# MOSTRA QUAIS CUIDADORES CUIDAM DO PACIENTE
@caregiver_patient_bp.route("/<int:user_id>", methods=["GET"])
@jwt_required()
@roles_required("admin")
def list_patient_caregivers(user_id):
    connection = None

    try:
        connection = connect()
        cursor = connection.cursor()

        # VERIFICA SE O ID INFORMADO COMO PACIENTE EXISTE
        patient, error, role_name = validate_user_role(cursor, user_id, "patient")

        # RETORNA O ERRO SE A ROLE NAO EXISTIR
        if error:
            return error_role(error, role_name, patient)

        # BUSCA OS CUIDADORES VINCULADOS
        caregivers =  get_caregivers_by_patient(cursor, user_id)

        if not caregivers:
            return jsonify([]), 200

        result = [dict(caregiver) for caregiver in caregivers]

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

    finally:
        if connection:
            connection.close()

#CUIDADOR CONSULTA OS PRÓPRIOS PACIENTES
@caregiver_patient_bp.route("/my-patients", methods=['GET'])
@jwt_required()
@roles_required("caregiver")
def my_patients():
    connection = None

    try:
        connection = connect()
        cursor = connection.cursor()

        caregiver_id = int(get_jwt_identity())

        
        patients = get_patients_by_caregiver(cursor, caregiver_id)

        if not patients:
            return jsonify([]), 200

        result = [dict(patient) for patient in patients]

        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

    finally:
        if connection:
            connection.close()

#PACIENTE CONSULTA OS PROPRIOS CUIDADORES
@caregiver_patient_bp.route("/my-caregivers", methods=['GET'])
@jwt_required()
@roles_required("patient")
def my_caregivers():
    connection = None

    try:
        connection = connect()
        cursor = connection.cursor()

        patient_id = int(get_jwt_identity())

        caregivers = get_caregivers_by_patient(cursor, patient_id)

        if not caregivers:
            return jsonify([]), 200

        result = [dict(caregiver) for caregiver in caregivers]

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

    finally:
        if connection:
            connection.close()

# REMOVE O VINCULO ENTRE CUIDADOR E PACIENTE
@caregiver_patient_bp.route("", methods=["DELETE"])
@jwt_required()
@roles_required("admin")
def remove_link():

    connection = None

    try:
        data = request.get_json()

        #VERIFICA SE FORAM ENVIADOS DADOS
        if not data:
            return jsonify({
                "error": "Dados não encontrados."
            }), 400

        #VERIFICA SE OS IDS FORAM INFORMADOS
        if not data.get("caregiver_id") or not data.get("patient_id"):
            return jsonify({
                "error": "OS IDs de cuidador e paciente são obrigatórios."
            }), 400
        
        connection = connect()
        cursor = connection.cursor()

        # BUSCA CUIDADOR E PACIENTE
        caregiver, error, role_name = validate_user_role(cursor, data["caregiver_id"], "caregiver")

        if error:
            return error_role(error, role_name, caregiver)
        
        patient, error, role_name = validate_user_role(cursor, data["patient_id"], "patient")

        if error:
            return error_role(error, role_name, patient)

        # VERIFICA SE O VINCULO EXISTE
        existing_link = get_caregiver_patient_link(cursor, data["caregiver_id"], data["patient_id"])

        if not existing_link:
            return jsonify({
                "error": "Vínculo não encontrado."
            }), 404
        
        if not existing_link["active"]:
            return jsonify({
                "error": "Vínculo já está inativo."
            }), 400

        # REMOVE O VINCULO
        disable_link(cursor, data["caregiver_id"], data["patient_id"])

        connection.commit()

        return jsonify({
            "message": "Vínculo removido com sucesso.",

            "disabled_link": {
                "caregiver": {
                    "id": caregiver["id"],
                    "name": caregiver["name"]
                },
                "patient": {
                    "id": patient["id"],
                    "name": patient["name"]
                }
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
