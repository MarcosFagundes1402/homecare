from flask import Blueprint, jsonify, request
from database.connect import connect
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.permissions import roles_required

from utils.response import (
    validate_required_fields,
    validate_non_empty_fields,
    error_role
    )

from utils.queries import (
    validate_user_role,
    get_caregiver_patient_link,
    get_active_medicine,
    register_medicine,
    get_user_by_id,
    get_medicines_data,
    get_medicines_by_patient_id,
    get_medicines_by_caregiver,
    validate_medicine,
    update_medicine,
    set_medicine_inactive
)

medicines_bp = Blueprint("medicines",__name__, url_prefix="/medicines")

#CRIA MEDICAMENTO PARA UM PACIENTE
@medicines_bp.route("", methods=['POST'])
@jwt_required()
@roles_required("admin")
def create_medicine():
    connection = None

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "error": "Dados não encontrados."
            }), 400

        required_fields = [
                    "patient_id",
                    "name",
                    "dosage",
                    "schedule_time"
                ]

        error = validate_required_fields(data, required_fields)

        if error:
            return jsonify({
                "error": error
            }), 400
 

        connection = connect()
        cursor = connection.cursor()

        #VERIFICA SE É PACIENTE
        patient, error, role_name = validate_user_role(cursor, data["patient_id"], "patient")

        if error:
            return error_role(error, role_name, patient)

        if not patient["active"]:
            return jsonify({
                "error": "Não é possivel cadastrar medicamento para paciente inativo."
            }), 400
        
        #VERIFICA SE O MEDICAMENTO JÁ ESTÁ CADASTRADO
        existing_medicine = get_active_medicine(cursor, data["patient_id"], data["name"], data["schedule_time"])

        if existing_medicine:
            return jsonify({
                "error": "Já existe medicamento cadastrado neste horário.",
                "medicine_id": existing_medicine["id"],
                "dosage": existing_medicine["dosage"],
                "suggestion": "Edite o medicamento existente caso queira alterar a dosagem."
            }), 409
        
        #CRIA O MEDICAMENTO
        medicine_id = register_medicine(
            cursor,
            data["patient_id"],
            data["name"],
            data["dosage"],
            data["schedule_time"],
            data.get("notes"),
        )

        connection.commit()

        return jsonify({
            "message": "Medicamento criado com sucesso.",

            "patient": {
                "id": patient["id"],
                "name": patient["name"]
            },

            "medicine":{
                "id": medicine_id,
                "name": data["name"],
                "dosage": data["dosage"],
                "schedule_time": data["schedule_time"],
                "notes": data.get("notes"),
                "active": True
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

#ADMIN CONSULTA TODOS OS MEDICAMENTOS
@medicines_bp.route("", methods=['GET'])
@jwt_required()
@roles_required("admin")
def list_medicines():
    connection = None

    try:
        connection = connect()
        cursor = connection.cursor()

        medicines = get_medicines_data(cursor)

        if not medicines:
            return jsonify({
                "medicines": []
            }), 200

        medicine_list = [dict(medicine) for medicine in medicines]

        return jsonify({
            "medicines": medicine_list
        }), 200

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500
    finally:
        if connection:
            connection.close()
        
# ADMIN CONSULTAR MEDICAMENTOS DE UM PACIENTE
@medicines_bp.route("/<int:patient_id>", methods=['GET'])
@jwt_required()
@roles_required("admin", "caregiver")
def list_patient_medicines(patient_id):
    connection = None

    try:
        connection = connect()
        cursor = connection.cursor()

        logged_user_id = int(get_jwt_identity())

        user = get_user_by_id(cursor, logged_user_id)
        
        if not user:
            return jsonify({
                "message": "Usuário não encontrado."
            }), 400

        logged_role = user["role"]

        # VERIFICA SE O USUÁRIO É PACIENTE
        patient, error, role_name = validate_user_role(cursor, patient_id, "patient")

        if error:
            return error_role(error, role_name, patient)

        # SE FOR CUIDADOR, PRECISA TER VINCULO COM O PACIENTE
        if logged_role == "caregiver":
            link = get_caregiver_patient_link(cursor, logged_user_id, patient_id)

            if not link or not link["active"]:
                 return jsonify ({
                     "error": "Você não possui vinculo com este paciente."
                 }), 403
            
        # BUSCA O MEDICAMENTO DO PACIENTE
        medicines = get_medicines_by_patient_id(cursor, patient_id)

        if not medicines:
            return jsonify({
                "patient": {
                    "id": patient["id"],
                    "name": patient["name"]
                },
                "medicines": []
            }), 200

        medicine_list = [dict(medicine) for medicine in medicines]

        return jsonify({
            "patient": {
                "id": patient["id"],
                "name": patient["name"]
            },
            "medicines": medicine_list
        }), 200

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

    finally:
        if connection:
            connection.close()


#PACIENTE CONSULTA OS PROPRIOS MEDICAMENTOS
@medicines_bp.route("/my-medicines", methods=['GET'])
@jwt_required()
@roles_required("patient")
def my_medicines():
    connection = None

    try:
        patient_id = int(get_jwt_identity())

        connection = connect()
        cursor = connection.cursor()

        #BUSCA PACIENTE LOGADO
        patient, error, role_name = validate_user_role(cursor, patient_id, "patient")

        # RETORNA O ERRO SE A ROLE NAO EXISTIR
        if error:
            return error_role(error, role_name, patient)

        #BUSCA O MEDICAMENTO DO PACIENTE
        medicines = get_medicines_by_patient_id(cursor, patient_id)

        if not medicines:
            return jsonify({
                "patient": {
                    "id": patient["id"],
                    "name": patient["name"]
                },
                "medicines": []
            }), 200

        medicine_list = [dict(medicine) for medicine in medicines]

        return jsonify({
            "patient":{
                "id": patient["id"],
                "name": patient["name"]
            },
            "medicines": medicine_list
        }), 200

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

    finally:
        if connection:
            connection.close()

#CUIDADOR VERIFICA OS MEDICAMENTOS DO SEUS PACIENTES
@medicines_bp.route("/my-patients-medicines", methods=['GET'])
@jwt_required()
@roles_required("caregiver")
def my_patients_medicines():
    connection = None

    try:
        caregiver_id = int(get_jwt_identity())

        connection = connect()
        cursor = connection.cursor()


        # VERIFICA SE O ID INFORMADO COMO CUIDADOR EXISTE
        caregiver, error, role_name = validate_user_role(cursor, caregiver_id, "caregiver")

        # RETORNA O ERRO SE A ROLE NAO EXISTIR
        if error:
            return error_role(error, role_name, caregiver)

        #BUSCAR OS MEDICAMENTOS DOS PACIENTES VINCULADOS
        medicines = get_medicines_by_caregiver(cursor, caregiver_id)

        if not medicines:
            return jsonify({
                "caregiver": {
                    "id": caregiver["id"],
                    "name": caregiver["name"]
                },
                "medicines": []
            }), 200

        medicine_list = []

        for medicine in medicines:
            medicine_list.append({
                "id": medicine["id"],
                "name": medicine["name"],
                "dosage": medicine["dosage"],
                "schedule_time": medicine["schedule_time"],
                "notes": medicine["notes"],
                "active": medicine["active"],

                "patient": {
                    "id": medicine["patient_id"],
                    "name": medicine["patient_name"]
                }
            })

        return jsonify({
            "caregiver": {
                "id": caregiver["id"],
                "name": caregiver["name"]
            },

            "medicines": medicine_list
        }), 200

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500
    
    finally:
        if connection:
            connection.close()
        
#EDITA UM MEDICAMENTO
@medicines_bp.route("/<int:medicine_id>", methods=['PATCH'])
@jwt_required()
@roles_required("admin")
def edit_medicine(medicine_id):
    connection = None

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "error": "Dados não encontrados."
            }), 400

        connection = connect()
        cursor = connection.cursor()

        #VERIFICA SE O MEDICAMENTO EXISTE
        medicine = validate_medicine(cursor, medicine_id)

        if not medicine:
            return jsonify({
                "error": "Medicamento não encontrado."
            }), 404

        #CAMPOS QUE PODE SER EDITADOS
        allowed_fields = [
            "name",
            "dosage",
            "schedule_time",
            "notes",
            "active"
        ]

        #VERIFICA SE FOI ENVIADO CAMPO NAO PERMITIDO
        for field in data:
            if field not in allowed_fields:
                return jsonify({
                    "error": f"O campo '{field}' não pode ser editado."
                }), 400

        #CAMPOS NAO PODEM FICAR VAZIOS
        non_empty_fields = [
            "name",
            "dosage",
            "schedule_time",
        ]

        error = validate_non_empty_fields(data, non_empty_fields)

        if error:
            return jsonify({
                "error": error
            }), 400
            
        fields = []
        values = []

        for field in allowed_fields:
            if field in data:
                fields.append(f"{field} = %s")
                values.append(data[field])

        #VERIFICA SE ALGUM CAMPO VÁLIDO FOI ENVIADO
        if not fields:
            return jsonify({
                "error": "Nenhum campo válido foi enviado para edição."
            }), 400

        #ATUALIZA TABELA DE MEDICAMENTOS
        update_medicine(cursor, medicine_id, fields, values)

        connection.commit()

        return jsonify({
            "message": "Medicamento atualizado com sucesso.",
            "medicine_id": medicine_id,
            "updated_fields": data
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

#EXCLUIR UM MEDICAMENTO
@medicines_bp.route("/<int:medicine_id>", methods=['DELETE'])
@jwt_required()
@roles_required("admin")
def disable_medicine(medicine_id):
    connection = None

    try:
        connection = connect()
        cursor = connection.cursor()

        #VERIFICAR SE O MEDICAMENTO EXISTE
        medicine = validate_medicine(cursor, medicine_id)

        if not medicine:
            return jsonify({
                "error": "Medicamento não encontrado."
            }), 404

        #VERIFICA SE JA ESTA INATIVO
        if not medicine["active"]:
            return jsonify({
                "error": "Este medicamento já está inativo."
            }), 400
            
        #DESATIVA O MEDICAMENTO
        set_medicine_inactive(cursor, medicine_id)

        connection.commit()

        return jsonify({
            "message": "Medicamento desativado com sucesso.",

            "medicine": {
                "id": medicine["id"],
                "name": medicine["name"],
                "patient_id": medicine["patient_id"]
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
    