from flask import jsonify, request, Blueprint
from database.connect import connect
from flask_jwt_extended import jwt_required
import sqlite3
from utils import (
    roles_required,
    buscar_role,
    error_role,
    cuidador_status,
    )

cuidadores_bp = Blueprint("cuidadores", __name__)

#CONSULTAR TODOS OS CUIDADORES
@cuidadores_bp.route("/cuidadores/consultar", methods=['GET'])
@jwt_required()
@roles_required("admin")
def list_caregivers():
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
                status,
            FROM cuidadores
        """)

        caregivers = cursor.fetchall()
        result = [dict(caregiver) for caregiver in caregivers]

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500
    
    finally:
        if connection:
            connection.close()

#CONSULTANDO CUIDADORES POR ID
@cuidadores_bp.route("/cuidadores/consultar/<int:id>", methods=['GET'])
@jwt_required()
@roles_required("admin")
def get_caregiver_by_id(caregiver_id):
    connection = None

    try:
        connection = connect()
        cursor = connection.cursor()

        #VALIDA SE O ID PERTENCE A UM CUIDADOR
        caregiver, error, role_name = buscar_role(cursor, caregiver_id, "cuidador")

        if error:
            return error_role(error, role_name, caregiver)

        #BUSCAR OS DADOS NO CUIDADOR
        cursor.execute("""
            SELECT
                id,
                cpf,
                data_nascimento,
                tel,
                endereco,
                obs,
                status
            FROM cuidadores
            WHERE id = ?
        """, (caregiver_id,))

        caregiver_data = cursor.fetchone()

        if not caregiver_data:
            return jsonify({
                "erro": "Cuidador não encontrado."
            }), 404

        return jsonify({
            "cuidador": {
                "id": caregiver["id"],
                "nome": caregiver["nome"],
                "cpf": caregiver_data["cpf"],
                "data_nascimento": caregiver_data["data_nascimento"],
                "tel": caregiver_data["tel"],
                "endereco": caregiver_data["endereco"],
                "obs": caregiver_data["obs"],
                "status": caregiver_data["status"]
            }
        }), 200

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if connection:
            connection.close()

#EDITAR CUIDADOR 
@cuidadores_bp.route("/cuidadores/editar/<int:id>", methods=['PATCH'])
@jwt_required()
@roles_required("admin")
def edit_caregiver(caregiver_id):
    connection = None

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "erro": "Dados não encontrados."
            }), 400

        connection = connect()
        cursor = connection.cursor()

        #VALIDA SE O ID PERTENCE A UM CUIDADOR
        caregiver, error, role_name = buscar_role(cursor, caregiver_id, "cuidador")

        if error:
            return error_role(error, role_name, caregiver)

        #CAMPOS QUE PODEM SER EDITADOS
        allowed_fields = [
            "cpf",
            "data_nascimento",
            "tel",
            "endereco",
            "obs"
        ]

        #VALIDA O CAMPO NAO PERMITIDOS
        for field in data:
            if field not in allowed_fields:
                return jsonify({
                    "erro": f"O campo '{field}' não pode ser editado."
                }), 400

        #VERIFICA CPF DUPLICADO
        if "cpf" in data:
            if data["cpf"] is None or data["cpf"].strip() == "":
                return jsonify({
                    "erro": "O campo 'cpf' não pode estar vazio."
                }), 400

            cursor.execute("""
                SELECT id
                FROM cuidadores
                WHERE cpf = ?
                AND id != ?
            """, (
                data["cpf"],
                caregiver_id
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

        values.append(caregiver_id)

        #ATUALIZAR CUIDADOR
        cursor.execute(f"""
            UPDATE cuidadores
            SET {", ".join(fields)}
            WHERE id = ?
        """, values)

        connection.commit()

        return jsonify({
            "msg": "Cuidador atualizado com sucesso.",
            "cuidador_id": caregiver_id,
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

#DESATIVAR CUIDADOR
@cuidadores_bp.route("/cuidadores/desativar/<int:id>", methods=['DELETE'])
@jwt_required()
@roles_required("admin")
def disable_caregiver(caregiver_id):
    connection = None

    try:
        connection = connect()
        cursor = connection.cursor()

        #VALIDA SE O ID PERTENCE A UM CUIDADOR
        caregiver, error, role_name = buscar_role(cursor, caregiver_id, "cuidador")

        if error:
            return error_role(error, role_name, caregiver)

        #VERIFICA STATUS DO CUIDADOR
        caregiver_registered = cuidador_status(cursor, caregiver_id)

        if not caregiver_registered:
            return jsonify({
                "erro": "Cuidador não encontrado."
            }), 404

        if caregiver_registered["status"] == "inativo":
            return jsonify({
                "erro": "Cuidador já inativo."
            }), 400

        #DESATIVA CUIDADOR
        cursor.execute("""
            UPDATE cuidadores
            SET status = 'inativo'
            WHERE id = ?
        """, (caregiver_id,))

        connection.commit()

        return jsonify({
            "msg": "Cuidador desativado com sucesso.",

            "cuidador": {
                "id": caregiver["id"],
                "nome": caregiver["nome"],
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