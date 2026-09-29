from flask import Blueprint, jsonify, request
from database.connect import connect
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.permissions import roles_required
from utils.response import error_role
from utils.queries import (
        caregiver_stats,
        patient_stats,
        get_caregiver_patient_link,
        validate_user_role,
    ) 


caregiver_patient_bp = Blueprint("cuidadores_pacientes", __name__)

# CRIA O VINCULO ENTRE CUIDADOR E PACIENTE
@caregiver_patient_bp.route("/cuidadores_pacientes/criar-vinculo", methods=["POST"])
@jwt_required()
@roles_required("admin")
def create_bond():

    connection = None

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "erro": "Dados não encontrados."
            }), 400

        if "cuidador_id" not in data or "paciente_id" not in data:
            return jsonify({
                "erro": "cuidador_id e paciente_id são obrigatórios."
            }), 400

        connection = connect()
        cursor = connection.cursor()

        # VERIFICA SE O ID INFORMADO COMO CUIDADOR EXISTE
        caregiver, error, role_name = validate_user_role(cursor, data["cuidador_id"], "caregiver")

        # RETORNA ERRO SE O USUARIO NAO EXISTIR OU A ROLE FOR INVALIDA
        if error:
            return error_role(error, role_name, caregiver)
        
        #VERIFICA SE EXISTE NA TABELA CUIDADORES
        registered_caregiver = caregiver_stats(cursor, data["cuidador_id"])

        if not registered_caregiver:
            return jsonify({
                "erro": "Cadastro de cuidador não encontrado."
            }), 404

        if registered_caregiver["status"] == "inativo":
            return jsonify({
                "erro": "Não é possível vincular um cuidador inativo."
            }), 400
        
        # VERIFICA SE O ID INFORMADO COMO PACIENTE EXISTE
        patient, error, role_name = validate_user_role(cursor, data["paciente_id"], "paciente")

        # RETORNA ERRO SE O USUARIO NAO EXISTIR OU A ROLE FOR INVALIDA
        if error:
            return error_role(error, role_name, patient)
        

        #VERIFICA SE EXISTE NA TABELA PACIENTES
        registered_patient = patient_stats(cursor, data["paciente_id"])

        if not registered_patient:
            return jsonify({
                "erro": "Cadastro de paciente não encontrado."
            }), 404

        if registered_patient["status"] == "inativo":
            return jsonify({
                "erro":"Não é possível vincular um paciente inativo."
            }), 400
        
        # VERIFICA SE O VINCULO JÁ EXISTE
        existing_link = get_caregiver_patient_link(cursor, data["cuidador_id"], data["paciente_id"])
 
        if existing_link:
            return jsonify({
                "erro": "Este cuidador já está vinculado a este paciente."
            }), 409

        # CRIA O VINCULO
        cursor.execute("""
            INSERT INTO cuidadores_pacientes (
                cuidador_id,
                paciente_id
            )
            VALUES (?, ?)
        """, (
            data["cuidador_id"],
            data["paciente_id"]
        ))

        connection.commit()

        return jsonify({
            "msg": "Vínculo criado com sucesso.",
            "cuidador": {
                "id": caregiver["id"],
                "nome": caregiver["nome"]
            },
            "paciente": {
                "id": patient["id"],
                "nome": patient["nome"]
            }
        }), 201

    except Exception as e:
        if connection:
            connection.rollback()

        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if connection:
            connection.close()


# MOSTRA OS PACIENTES QUE O CUIDADOR TEM
@caregiver_patient_bp.route("/cuidadores_pacientes/consultar-cuidador/<int:id>", methods=["GET"])
@jwt_required()
@roles_required("admin")
def list_caregiver_patients(caregiver_id):

    connection = None

    try:
        connection = connect()
        cursor = connection.cursor()

        # VERIFICA SE O ID INFORMADO COMO CUIDADOR EXISTE
        caregiver, error, role_name = validate_user_role(cursor, caregiver_id, "cuidador")

        # RETORNA O ERRO SE A ROLE NAO EXISTIR
        if error:
            return error_role(error, role_name, caregiver)

   
        # BUSCA OS PACIENTES VINCULADOS
        cursor.execute("""
                SELECT
                    pacientes.id,
                    pacientes.nome,
                    pacientes.cpf,
                    pacientes.data_nascimento,
                    pacientes.tel,
                    pacientes.endereco,
                    pacientes.obs
                FROM cuidadores_pacientes
                JOIN pacientes
                    ON cuidadores_pacientes.paciente_id = pacientes.id
                WHERE cuidadores_pacientes.cuidador_id = ?
            """, (caregiver_id,))

        patients = cursor.fetchall()

        if not patients:
            return jsonify([]), 200

        result = [dict(patient) for patient in patients]

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if connection:
            connection.close()

# MOSTRA QUAIS CUIDADORES CUIDAM DO PACIENTE
@caregiver_patient_bp.route("/cuidadores_pacientes/consultar-paciente/<int:id>", methods=["GET"])
@jwt_required()
@roles_required("admin")
def list_patient_caregivers(patient_id):
    connection = None

    try:
        connection = connect()
        cursor = connection.cursor()

        # VERIFICA SE O ID INFORMADO COMO PACIENTE EXISTE
        patient, error, role_name = validate_user_role(cursor, patient_id, "paciente")

        # RETORNA O ERRO SE A ROLE NAO EXISTIR
        if error:
            return error_role(error, role_name, patient)

        # BUSCA OS CUIDADORES VINCULADOS
        cursor.execute("""
            SELECT
                cuidadores.id,
                cuidadores.nome,
                cuidadores.cpf,
                cuidadores.data_nascimento,
                cuidadores.tel,
                cuidadores.endereco,
                cuidadores.obs,
                cuidadores.status

            FROM cuidadores_pacientes

            JOIN cuidadores
                ON cuidadores_pacientes.cuidador_id = cuidadores.id

            WHERE cuidadores_pacientes.paciente_id = ?
        """, (patient_id,))

        caregivers = cursor.fetchall()

        if not caregivers:
            return jsonify([]), 200

        result = [dict(caregiver) for caregiver in caregivers]

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if connection:
            connection.close()

#CUIDADOR CONSULTA OS PRÓPRIOS PACIENTES
@caregiver_patient_bp.route("/cuidadores_pacientes/meus-pacientes", methods=['GET'])
@jwt_required()
@roles_required("cuidador")
def my_patients():
    connection = None

    try:
        connection = connect()
        cursor = connection.cursor()

        caregiver_id = int(get_jwt_identity())

        cursor.execute("""
            SELECT 
                pacientes.id,
                pacientes.nome,
                pacientes.cpf,
                pacientes.data_nascimento,
                pacientes.tel,
                pacientes.endereco,
                pacientes.obs,
                pacientes.status
            FROM cuidadores_pacientes
            JOIN pacientes
                ON cuidadores_pacientes.paciente_id = pacientes.id
            WHERE cuidadores_pacientes.cuidador_id = ?
        """, (caregiver_id,))

        patients = cursor.fetchall()

        if not patients:
            return jsonify([]), 200

        result = [dict(patient) for patient in patients]

        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if connection:
            connection.close()

#PACIENTE CONSULTA OS PROPRIOS CUIDADORES
@caregiver_patient_bp.route("/cuidadores_pacientes/meus-cuidadores", methods=['GET'])
@jwt_required()
@roles_required("paciente")
def my_caregivers():
    connection = None

    try:
        connection = connect()
        cursor = connection.cursor()

        patient_id = int(get_jwt_identity())

        cursor.execute("""
            SELECT 
                cuidadores.id,
                cuidadores.nome,
                cuidadores.cpf,
                cuidadores.data_nascimento,
                cuidadores.tel,
                cuidadores.endereco,
                cuidadores.obs,
                cuidadores.status

            FROM cuidadores_pacientes
            
            JOIN cuidadores
                ON cuidadores_pacientes.cuidador_id = cuidadores.id
            WHERE cuidadores_pacientes.paciente_id = ?
        """, (patient_id,))

        caregivers = cursor.fetchall()

        if not caregivers:
            return jsonify([]), 200

        result = [dict(caregiver) for caregiver in caregivers]

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if connection:
            connection.close()

# REMOVE O VINCULO ENTRE CUIDADOR E PACIENTE
@caregiver_patient_bp.route("/cuidadores_pacientes/desativar-vinculo", methods=["DELETE"])
@jwt_required()
@roles_required("admin")
def remove_link():

    connection = None

    try:
        data = request.get_json()

        #VERIFICA SE FORAM ENVIADOS DADOS
        if not data:
            return jsonify({
                "erro": "Dados não encontrados."
            }), 400

        #VERIFICA SE OS IDS FORAM INFORMADOS
        if not data.get("cuidador_id") or not data.get("paciente_id"):
            return jsonify({
                "erro": "cuidador_id e paciente_id são obrigatórios."
            }), 400
        
        connection = connect()
        cursor = connection.cursor()

        # BUSCA CUIDADOR E PACIENTE
        caregiver, error, role_name = validate_user_role(cursor, data["cuidador_id"], "cuidador")

        if error:
            return error_role(error, role_name, caregiver)
        
        patient, error, role_name = validate_user_role(cursor, data["paciente_id"], "paciente")

        if error:
            return error_role(error, role_name, patient)

        # VERIFICA SE O VINCULO EXISTE
        existing_link = get_caregiver_patient_link(cursor, data["cuidador_id"], data["paciente_id"])

        if not existing_link:
            return jsonify({
                "erro": "Vínculo não encontrado."
            }), 404

        # REMOVE O VINCULO
        cursor.execute("""
            DELETE FROM cuidadores_pacientes
            WHERE cuidador_id = ?
            AND paciente_id = ?
        """, (
            data["cuidador_id"],
            data["paciente_id"]
        ))

        connection.commit()

        return jsonify({
            "msg": "Vínculo removido com sucesso.",

            "vinculo_removido": {
                "cuidador": {
                    "id": caregiver["id"],
                    "nome": caregiver["nome"]
                },
                "paciente": {
                    "id": patient["id"],
                    "nome": patient["nome"]
                }
            }
        }), 200

    except Exception as e:
        if connection:
            connection.rollback()

        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if connection:
            connection.close()
