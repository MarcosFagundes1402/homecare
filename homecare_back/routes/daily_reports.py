from flask import Blueprint, jsonify, request
from database.connect import connect
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from utils.permissions import roles_required

from utils.response import (
    validate_required_fields,
    validate_non_empty_fields,
    error_role
)
from utils.queries import (
    get_user_by_id,
    validate_user_role,
    get_caregiver_patient_link,
    register_daily_report,
    fetch_daily_reports_by_patient,
    fetch_all_daily_reports,
    update_daily_report,
    fetch_daily_report_by_id,
    set_daily_report_inactive
)

daily_reports_bp = Blueprint("daily_reports", __name__, url_prefix="/daily-reports")

@daily_reports_bp.route("", methods=['POST'])
@jwt_required()
@roles_required("admin", "caregiver")
def create_daily_reports():
    connection = None

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "error": "Dados não encontrados."
            }), 400

        # CAMPOS OBRIGATÓRIOS
        required_fields = [
            "patient_id",
            "hygiene",
            "observations"
        ]

        error = validate_required_fields(data, required_fields)

        if error:
            return jsonify({
                "error": error
            }), 400

        user_id = int(get_jwt_identity())

        connection = connect()
        cursor = connection.cursor()

        #BUSCAR O USUARIO LOGADO
        user = get_user_by_id(cursor, user_id)

        if not user:
            return jsonify({
                "error": "Usuário não encontrado."
            }), 404

        #VERIFICA SE O PACIENTE EXISTE
        patient, error, role_name = validate_user_role(cursor, data["patient_id"], "patient")

        if error:
            return error_role(error, role_name, patient)

        if not patient["active"]:
            return jsonify({
                "error": "Não é possível criar um relatório para paciente inativo."
            }), 400

        #SE FOR CUIDADOR, VERIFICA SE ESTÁ VINCULADO AO PACIENTE
        if user["role"].lower() == "caregiver":
            existing_link = get_caregiver_patient_link(cursor, user_id, data["patient_id"])

        elif user["role"].lower() == "admin":
            if "caregiver_id" not in data:
                return jsonify({
                    "error": "caregiver_id é obrigátorio para admin."
                }), 400

            caregiver, error, role_name = validate_user_role(cursor, data["caregiver_id"], "caregiver")

            if error:
                return error_role(error, role_name, caregiver)

            if not caregiver["active"]:
                return jsonify({
                    "error": "Cuidador está inativo."
                }), 400

            existing_link = get_caregiver_patient_link(cursor, data["caregiver_id"], data["patient_id"])

        if not existing_link or not existing_link["active"]:
            return jsonify({
                "error": "Cuidador não possui um vínculo ativo com este paciente."
            }), 403

        link_id = existing_link["id"]

        # NORMALIZA OS CMAPOS OPCIONAIS
        blood_pressure = str(data.get("blood_pressure", "")).strip() or "não aferido"
        glucose = str(data.get("glucose", "")).strip() or "não aferido"
        temperature = str(data.get("temperature", "")).strip() or "não aferido"

        report_id = register_daily_report(
            cursor,
            link_id,
            user_id,
            data.get("food"),
            data.get("hygiene"),
            blood_pressure,
            glucose,
            temperature,
            data.get("observations")
        )

        connection.commit()

        return jsonify({
                "message": "Relatório diário criado com sucesso.",

                    "report": {
                        "id": report_id,
                        "link_id": link_id,
                        "patient_id": data["patient_id"],
                        "created_by_user_id": user_id,
                        "food": data.get("food"),
                        "hygiene": data.get("hygiene"),
                        "blood_pressure": blood_pressure,
                        "glucose": glucose,
                        "temperature": temperature,
                        "observations": data.get("observations")
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

#LISTAR RELATÓRIOS DIÁRIOS POR PACIENTE
@daily_reports_bp.route("/<int:patient_id>", methods=['GET'])
@jwt_required()
@roles_required("admin", "caregiver")
def get_patient_daily_reports(patient_id):
    connection = None

    try:
        user_id = int(get_jwt_identity())

        connection = connect()
        cursor = connection.cursor()

        #BUSCAR USUARIO LOGADO
        user = get_user_by_id(cursor, user_id)

        if not user:
            return jsonify({
                "error": "Usuário não encontrado."
            }), 404

        #VERIFICA SE O PACIENTE EXISTE
        patient, error, role_name = validate_user_role(cursor, patient_id, "patient")

        if error:
            return error_role(error, role_name, patient)

        #VERIFICA VINCULO ENTRE CUIDADOR E PACIENTE
        if user["role"].lower() == "caregiver":
            existing_link = get_caregiver_patient_link(cursor, user_id, patient_id)

            if not existing_link or not existing_link["active"]:
                return jsonify({
                    "error": "Cuidador não possui vínculo ativo com este paciente."
                }), 403

        #BUSCA RELATORIOS
        daily_reports = fetch_daily_reports_by_patient(cursor, patient_id)

        if not daily_reports:
            return jsonify({
                "patient": {
                    "id": patient["id"],
                    "name": patient["name"]
                },
                "reports": []
            }), 200

        report_list = []

        for daily_report in daily_reports:
            report_list.append({
                "id": daily_report["id"],
                "food": daily_report["food"],
                "hygiene": daily_report["hygiene"],
                "blood_pressure": daily_report["blood_pressure"],
                "glucose": daily_report["glucose"],
                "temperature": daily_report["temperature"],
                "observations": daily_report["observations"],
                "report_time": daily_report["report_time"],
                "report_date": daily_report["report_date"],

                "created_by_user": {
                    "id": daily_report["created_by_user_id"],
                    "name": daily_report["created_by_user_name"],
                    "role": daily_report["created_by_user_role"]
                }
            })

        return jsonify({
            "patient": {
                "id": patient["id"],
                "name": patient["name"]
            },

            "reports": report_list
        }), 200

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

    finally:
        if connection:
             connection.close()

# LISTAR TODOS OS RELATORIOS DIARIOS
@daily_reports_bp.route("", methods=['GET'])
@jwt_required()
@roles_required("admin")
def list_daily_reports():
    connection = None

    try:
        connection = connect()
        cursor = connection.cursor()

        #BUSCA TODOS OS RELATORIOS
        daily_reports = fetch_all_daily_reports(cursor)

        if not daily_reports:
            return jsonify({
                "reports": []
            }), 200

        report_list = []

        for daily_report in daily_reports:
            report_list.append({
                "id": daily_report["id"],

                "patient": {
                    "id": daily_report["patient_id"],
                    "name": daily_report["patient_name"]
                },

                "food": daily_report["food"],
                "hygiene": daily_report["hygiene"],
                "blood_pressure": daily_report["blood_pressure"],
                "glucose": daily_report["glucose"],
                "temperature": daily_report["temperature"],
                "observations": daily_report["observations"],
                "report_time": daily_report["report_time"],
                "report_date": daily_report["report_date"],

                "created_by_user": {
                    "id": daily_report["created_by_user_id"],
                    "name": daily_report["created_by_user_name"],
                    "role": daily_report["created_by_user_role"]
                }
            })

        return jsonify({
            "reports": report_list
        }), 200

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

    finally:
        if connection:
            connection.close()

#EDITAR RELATORIO DIARIO
@daily_reports_bp.route("/<int:report_id>", methods=['PATCH'])
@jwt_required()
@roles_required("admin", "caregiver")
def edit_daily_report(report_id):
    connection = None

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "error": "Dados não encontrados."
            }), 400

        user_id = int(get_jwt_identity())

        connection = connect()
        cursor = connection.cursor()

        #BUSCA USUARIO LOGADO
        user = get_user_by_id(cursor, user_id)

        if not user:
            return jsonify({
                "error": "Usuário não encontrado."
            }), 404

        #BUSCAR O RELATORIO
        daily_report = fetch_daily_report_by_id(cursor, report_id)

        if not daily_report:
            return jsonify({
                "error": "Relatório não encontrado."
            }), 404

        #CUIDADOR SO PODE EDITAR RELATORIO QUE ELE MESMO CRIOU
        if user["role"].lower() == "caregiver":

            if daily_report["created_by_user_id"] != user_id:
                return jsonify({
                    "error": "Cuidador não pode editar relatório criado por outro usuário."
                }), 403

            # VERIFICA SE AINDA POSSUI VÍNCULO COM O PACIENTE
            existing_link = get_caregiver_patient_link(cursor, user_id, daily_report["patient_id"])

            if not existing_link or not existing_link["active"]:
                return jsonify({
                    "error": "Cuidador não possui vínculo ativo com este paciente."
                }), 403


        #CAMPOS QUE PODER SER EDITADOS
        allowed_fields = [
            "food",
            "hygiene",
            "blood_pressure",
            "glucose",
            "temperature",
            "observations"
        ]

        for field in data:
            if field not in allowed_fields:
                return jsonify({
                    "error": f"O campo '{field}' não pode ser editado."
                }), 400

        #CAMPOS QUE NAO PODE FICAR VAZIO
        non_empty_fields = [
            "hygiene",
            "observations"
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

        if not fields:
            return jsonify({
                "error": "Nenhum campo válido foi enviado para edição."
            }), 400

        #ATUALIZA O RELATORIO
        update_daily_report(cursor, report_id, fields, values)

        connection.commit()

        return jsonify({
            "message": "Relatório atualizado com sucesso."
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

#DESATIVAR RELATORIOS DIARIO
@daily_reports_bp.route("/disable/<int:report_id>", methods=['DELETE'])
@jwt_required()
@roles_required("admin")
def disable_daily_report(report_id):
    connection = None

    try:
        connection = connect()
        cursor = connection.cursor()

        #VERIFICAR SE O RELATORIO EXISTE
        daily_report = fetch_daily_report_by_id(cursor, report_id)

        if not daily_report:
            return jsonify({
                "error": "Relatório não encontrado."
            }), 404

        if not daily_report["active"]:
            return jsonify({
                "error": "Este relatório já está inativo."
            }), 400

        #DESATIVA O RELATORIO
        set_daily_report_inactive(cursor, report_id)

        connection.commit()

        return jsonify(
            {
                "message": "Relatório desativado com sucesso.",
                "inactive_report": {
                    "id": daily_report["id"],
                    "patient_id": daily_report["patient_id"],
                    "created_by_user_id": daily_report["created_by_user_id"],
                    "food": daily_report["food"],
                    "hygiene": daily_report["hygiene"],
                    "blood_pressure": daily_report["blood_pressure"],
                    "glucose": daily_report["glucose"],
                    "temperature": daily_report["temperature"],
                    "observations": daily_report["observations"],
                    "report_time": daily_report["report_time"],
                    "report_date": daily_report["report_date"],
                    "active": False,
                },
            }
        ), 200

    except Exception as e:
        if connection:
            connection.rollback()

        return jsonify({
            "error": str(e)
        }), 500

    finally:
        if connection:
            connection.close()
