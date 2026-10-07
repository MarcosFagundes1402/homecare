from flask import jsonify, request, Blueprint
from database.connect import connect
from flask_jwt_extended import jwt_required
import sqlite3
from utils.permissions import roles_required
from utils.response import validate_non_empty_fields, error_role

from utils import (
    validate_user_role,
    error_role,
    )

patient_bp = Blueprint("pacientes", __name__)

# CONSULTADO TODOS PACIENTES
@patient_bp.route("/pacientes/consultar", methods=['GET'])
@jwt_required()
@roles_required("admin")
def list_patients():

    connection = None

    try: 
        connection = connect()
        cursor = connection.cursor()

        cursor.execute(""" 
            SELECT
                id,
                nome,
                cpf,
                data_nascimento,
                tel,
                endereco,
                obs,
                status
            FROM pacientes
        """)

        patients = cursor.fetchall()

        patients_list = [dict(patient) for patient in patients]

        return jsonify (patients_list), 200

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if connection:
            connection.close()

#CONSULTANDO PACIENTES POR ID
@patient_bp.route('/pacientes/consultar/<int:id>', methods=['GET'])
@jwt_required()
@roles_required("admin")
def get_patient_by_id(patient_id):
    connection = None

    try:
        connection = connect()
        cursor = connection.cursor()

        #VALIDA SE O ID PERTENCE A UM PACIENTE
        patient, error, role_name = validate_user_role(cursor, patient_id, "paciente")

        if error:
            return error_role(error, role_name, patient)

        #BUSCA OS DADOS DO PACIENTE
        cursor.execute("""
            SELECT 
                id,
                cpf,
                data_nascimento,
                tel,
                endereco,
                obs,
                status
            FROM pacientes
            WHERE id = ?
        """, (patient_id, ))

        patient_data = cursor.fetchone()

        if not patient_data:
            return jsonify({
                "erro": "Paciente não encontrado."
            }), 404

        return jsonify({
            "paciente": {
                "id": patient["id"],
                "nome": patient["nome"],
                "cpf": patient_data["cpf"],
                "data_nascimento": patient_data["data_nascimento"],
                "tel": patient_data["tel"],
                "endereco": patient_data["endereco"],
                "obs": patient_data["obs"],
                "status": patient_data["status"]
            }
        }), 200

    except Exception as e:
        return jsonify ({
            "erro": str(e)
        }), 500

    finally:
        if connection:
            connection.close()

#EDITAR PACIENTE
@patient_bp.route('/pacientes/editar/<int:id>', methods=['PATCH'])
@jwt_required()
@roles_required("admin")
def edit_patient(patient_id):

    connection = None

    try: 
        data = request.get_json()

        if not data:
            return jsonify({
                "erro": "Dados não encontrados."
            }), 400

        
        connection = connect()
        cursor = connection.cursor()

        #VALIDA SE O ID PERTENCE A UM PACIENTE
        patient, error, role_name = validate_user_role(cursor, patient_id, "paciente")

        if error:
            return error_role(error, role_name, patient)

        #CAMPOS QUE PODEM SER EDITADOS
        allowed_fields = [
            "cpf",
            "data_nascimento",
            "tel",
            "endereco",
            "obs"
        ]

        for field in data:
            if field not in allowed_fields:
                return jsonify({
                    "erro": f"O campo '{field}' não pode ser editado."
                }), 400

        #CAMPOS QUE NÃO PODEM FICAR VAZIOS
        non_empty_fields = [
            "cpf",
            "data_nascimento",
            "tel",
            "endereco"
        ]

        error = validate_non_empty_fields(data, non_empty_fields)

        if error:
            return jsonify({
                "erro": error
            }), 400

        #SE O CPF ENVIADO, VERIFICA DUPLICIDADE
        if "cpf" in data:
            cursor.execute("""
                SELECT id
                FROM pacientes
                WHERE cpf = ?
                AND id != ?
            """, (
                data["cpf"],
                patient_id
            ))

            existing_cpf = cursor.fetchone()

            if existing_cpf:
                return jsonify({
                    "erro": "CPF já cadastrado."
                }), 400

        #MONTA UPDATE DINAMICO
        fields = []
        values = []

        for field in allowed_fields:
            if field in data:
                fields.append(f"{field} = ?")
                values.append(data[field])

        if not fields:
            return jsonify({
                "erro": "Nenhum campo válido foi enviado para edição."
            }), 400

        values.append(patient_id)

        #ATUALIZA PACIENTE
        cursor.execute(f"""
            UPDATE pacientes
            SET {", ".join(fields)}
            WHERE id = ?
        """, values)

        connection.commit()

        return jsonify({
            "msg": "Paciente atualizado com sucesso.",
            "paciente_id": patient_id,

            "campos_atualizados": data
        }), 200
        
    except sqlite3.IntegrityError:
        if connection:
            connection.rollback()

        return jsonify({
            "erro": "CPF já cadastrado."
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

# DESATIVAR PACIENTE 
@patient_bp.route('/pacientes/desativar/<int:id>', methods=['DELETE'])
@jwt_required()
@roles_required("admin")
def disable_patient(patient_id):

    connection = None

    try:
        connection = connect()
        cursor = connection.cursor()

        patient, error, role_name = validate_user_role(cursor, patient_id, "paciente")

        if error:
            return error_role(error, role_name, patient)
        
        registered_patient = patient_stats(cursor, patient_id)

        if not registered_patient:
            return jsonify({
                "erro": "Paciente não encontrado."
            }), 404

        if registered_patient["status"] == "inativo":
            return jsonify({
                "erro": "Paciente já inativo."
            }), 400
        
        cursor.execute("""
            UPDATE pacientes
            SET status = 'inativo'
            WHERE id = ?
        """, (patient_id,))

        connection.commit()

        return jsonify({
            "msg": "Paciente desativado com sucesso.",

            "paciente": {
                "id": patient["id"],
                "nome": patient["nome"],
                "status": "inativo"
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