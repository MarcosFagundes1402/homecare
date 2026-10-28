from database.connect import connect
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from utils.permissions import roles_required
from utils.queries import (
    create_medicine_administration,
    fetch_all_medicine_administrations,
    fetch_medicine_administration_by_id,
    fetch_medicine_administrations_by_caregiver,
    fetch_medicine_administrations_by_patient,
    get_caregiver_patient_link,
    get_existing_administration,
    get_user_by_id,
    set_medicine_administration_inactive,
    update_medicine_administration,
    validate_medicine,
    validate_user_role,
    fetch_medicine_administrations_by_caregiver_and_patient
)
from utils.response import (
    error_role,
    validate_non_empty_fields,
    validate_required_fields,
)

administration_medications_bp = Blueprint(
    "medicine_administration", __name__, url_prefix="/medicine_adminitration"
)


# CRIA O REGISTRO DA ADMINISTRACAO DO MEDICAMENTO
@administration_medications_bp.route("", methods=["POST"])
@jwt_required()
@roles_required("admin", "caregiver")
def register_administration():

    connection = None

    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Dados não encontrados."}), 400

        # CAMPOS OBRIGATÓRIOS
        required_fields = [
            "medicine_id",
            "patient_id",
            "dosage_given",
        ]

        # VALIDA OS CAMPOS OBRIGATORIOS
        error = validate_required_fields(data, required_fields)

        if error:
            return jsonify({"error": error}), 400

        # PEGA O ID DO USUÁRIO LOGADO
        user_id = int(get_jwt_identity())

        connection = connect()
        cursor = connection.cursor()

        # VERIFICA QUEM ESTÁ LOGADO
        user = get_user_by_id(cursor, user_id)

        if not user:
            return jsonify({"error": "Usuário não encontrado."}), 404

        # VERIFICA SE O MEDICAMENTO EXISTE
        medicine = validate_medicine(cursor, data["medicine_id"])

        if not medicine:
            return jsonify({"error": "Medicamento não encontrado."}), 404

        # VERIFICA SE O MEDICAMENTO PERTENCE AO PACIENTE
        if medicine["patient_id"] != data["patient_id"]:
            return jsonify(
                {"error": "Este medicamento não pertence ao paciente informado."}
            ), 400

        # VERIFICA SE O MEDICAMENTO ESTÁ ATIVO
        if not medicine["active"]:
            return jsonify(
                {
                    "error": "Não é possível registrar administração de medicamento inativo."
                }
            ), 400

        # VERIFICA SE O CUIDADOR ESTÁ VINCULADO AO PACIENTE
        if user["role"].lower() == "caregiver":
            bond = get_caregiver_patient_link(cursor, user_id, data["patient_id"])

            if not bond or not bond["active"]:
                return jsonify(
                    {"error": "Cuidador não possui vínculo ativo com este paciente."}
                ), 403

            link_id = bond["id"]

        elif user["role"].lower() == "admin":
            if "caregiver_id" not in data:
                return jsonify({"error": "caregiver_id é obrigatório para admin."}), 400

            caregiver, error, role_name = validate_user_role(
                cursor, data["caregiver_id"], "caregiver"
            )

            if error:
                return error_role(error, role_name, caregiver)

            if not caregiver["active"]:
                return jsonify({"error": "Cuidador está inativo."}), 400

            bond = get_caregiver_patient_link(
                cursor, data["caregiver_id"], data["patient_id"]
            )

            if not bond or not bond["active"]:
                return jsonify(
                    {"error": "Não existe vínculo ativo entre cuidador e paciente."}
                ), 403

            link_id = bond["id"]

        # VERIFICA SE JÁ EXISTE ADMINISTRACAO NO MESMO HORARIO
        existing_administration = get_existing_administration(
            cursor, data["medicine_id"], link_id
        )

        if existing_administration:
            return jsonify(
                {
                    "error": "Já existe uma administração deste medicamento no mesmo horário."
                }
            ), 409

        # REGISTRAR A ADMINISTRAÇÃO DO MEDICAMENTO
        administration_id = create_medicine_administration(
            cursor,
            data["medicine_id"],
            link_id,
            user_id,
            data["dosage_given"],
            data.get("notes"),
        )

        connection.commit()

        return jsonify(
            {
                "message": "Administração registrada com sucesso.",
                "administration": {
                    "id": administration_id,
                    "dosage_given": data["dosage_given"],
                    "schedule_time": data["schedule_time"],
                    "notes": data.get("notes"),
                },
                "medicine": {"id": medicine["id"], "name": medicine["name"]},
                "patient_id": data["patient_id"],
                "created_by_user": {
                    "id": user["id"],
                    "name": user["name"],
                    "role": user["role"],
                },
                "active": True,
            }
        ), 201

    except Exception as e:
        if connection:
            connection.rollback()

        return jsonify({"error": str(e)}), 500

    finally:
        if connection:
            connection.close()


# LISTAR TODOS AS ADMINISTRAÇÕES
@administration_medications_bp.route("", methods=["GET"])
@jwt_required()
@roles_required("admin")
def list_administrations():

    connection = None

    try:
        connection = connect()
        cursor = connection.cursor()

        administrations = fetch_all_medicine_administrations(cursor)

        administration_list = []

        for administration in administrations:
            administration_list.append(
                {
                    "id": administration["id"],
                    "patient": {
                        "id": administration["patient_id"],
                        "name": administration["patient_name"],
                    },
                    "medicine": {
                        "id": administration["medicine_id"],
                        "name": administration["medicine_name"],
                    },
                    "dosage_given": administration["dosage_given"],
                    "notes": administration["notes"],
                    "administration_date": administration["administration_date"],
                    "administration_time": administration["administration_time"],
                    "active": administration["active"],
                    "created_by_user": {
                        "id": administration["created_by_user_id"],
                        "name": administration["created_by_user_name"],
                        "role": administration["created_by_user_role"],
                    },
                }
            )

        return jsonify({"administrations": []}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if connection:
            connection.close()


# PACIENTE CONSULTA O PROPRIO HISTORICO
@administration_medications_bp.route("", methods=["GET"])
@jwt_required()
@roles_required("patient")
def my_administrations():
    connection = None

    try:
        patient_id = int(get_jwt_identity())

        connection = connect()
        cursor = connection.cursor()

        # VALIDA O PACIENTE LOGADO
        patient, error, role_name = validate_user_role(cursor, patient_id, "patient")

        if error:
            return error_role(error, role_name, patient)

        # BUSCAR AS ADMINISTRACOES DO PACIENTE
        administrations = fetch_medicine_administrations_by_patient(cursor, patient_id)

        if not administrations:
            return jsonify(
                {
                    "patient": {"id": patient["id"], "name": patient["name"]},
                    "administrations": [],
                }
            ), 200

        result = []

        for administration in administrations:
            result.append(
                {
                    "id": administration["id"],
                    "medicine": {
                        "id": administration["medicine_id"],
                        "name": administration["medicine_name"],
                    },
                    "dosage_given": administration["dosage_given"],
                    "administration_date": administration["administration_date"],
                    "administration_time": administration["administration_time"],
                    "notes": administration["notes"],
                    "active": administration["active"],
                    "created_by_user": {
                        "id": administration["created_by_user_id"],
                        "name": administration["created_by_user_name"],
                        "role": administration["created_by_user_role"],
                    },
                }
            )

        return jsonify(
            {
                "patient": {"id": patient["id"], "name": patient["name"]},
                "administrations": result,
            }
        ), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if connection:
            connection.close()


# CUIDADOR CONSULTA O HISTORICO DOS PROPRIOS PACIENTES
@administration_medications_bp.route("", methods=["GET"])
@jwt_required()
@roles_required("caregiver")
def my_patients_history():
    connection = None

    try:
        caregiver_id = int(get_jwt_identity())

        connection = connect()
        cursor = connection.cursor()

        # BUSCA AS ADMINISTRACOES DOS PACIENTES VINCULADOS AO CUIDADOR
        administrations = fetch_medicine_administrations_by_caregiver(
            cursor, caregiver_id
        )

        if not administrations:
            return jsonify({"administrations": []}), 200

        result = []

        for administration in administrations:
            result.append(
                {
                    "id": administration["id"],
                    "patient": {
                        "id": administration["patient_id"],
                        "name": administration["patient_name"],
                    },
                    "medicine": {
                        "id": administration["medicine_id"],
                        "name": administration["medicine_name"],
                    },
                    "schedule_time": administration["schedule_time"],
                    "administration_date": administration["administration_date"],
                    "administration_time": administration["administration_time"],
                    "dosage_given": administration["dosage_given"],
                    "notes": administration["notes"],
                    "active": administration["active"],
                    "created_by_user": {
                        "id": administration["created_by_user_id"],
                        "name": administration["created_by_user_name"],
                        "role": administration["created_by_user_role"],
                    },
                }
            )

        return jsonify({"administrations": result}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if connection:
            connection.close()


# EDITAR ADMINISTRACAO DE MEDICAMENTOS
@administration_medications_bp.route("/<int:administration_id>", methods=["PATCH"])
@jwt_required()
@roles_required("admin", "caregiver")
def edit_administration(administration_id):
    connection = None

    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Dados não encontrados."}), 400

        user_id = int(get_jwt_identity())

        connection = connect()
        cursor = connection.cursor()

        # BUSCA O USUARIO LOGADO
        user = get_user_by_id(cursor, user_id)

        if not user:
            return jsonify({"error": "Usuário não encontrado."}), 404

        # BUSCA A ADMINISTRACAO
        administration = fetch_medicine_administration_by_id(cursor, administration_id)

        if not administration:
            return jsonify({"error": "Administração não encontrada."}), 404

        # SE FOR CUIDADOR, SÓ PODE EDITAR O QUE ELE MESMO REGISTROU
        if (
            user["role"].lower() == "caregiver"
            and administration["created_by_user_id"] != user_id
        ):
            return jsonify(
                {
                    "error": "Cuidador não pode editar administração registrada por outro cuidador."
                }
            ), 403

        # CAMPOS OBRIGATORIOS
        required_fields = ["dosage_given", "notes"]

        error = validate_required_fields(data, required_fields)

        if error:
            return jsonify({"error": error}), 400

        # CAMPOS QUE NAO PODEM ESTAR VAZIO
        non_empty_fields = ["dosage_given", "notes"]

        error = validate_non_empty_fields(data, non_empty_fields)

        if error:
            return jsonify({"error": error}), 400

        fields = []
        values = []

        for field in required_fields:
            fields.append(f"{field} = %s")
            values.append(data[field])

        values.append(administration_id)

        # ATUALIZA A ADMINISTRACAO
        update_medicine_administration(cursor, fields, values)
        connection.commit()

        return jsonify(
            {
                "message": "Administração atualizada com sucesso.",
                "administration": administration_id,
                "updated_fields": data,
            }
        ), 200

    except Exception as e:
        if connection:
            connection.rollback()

        return jsonify({"error": str(e)}), 500

    finally:
        if connection:
            connection.close()


# DESATIVAR REGISTRO DE ADMINISTRACAO
@administration_medications_bp.route("/<int:administration_id>", methods=["DELETE"])
@jwt_required()
@roles_required("admin", "caregiver")
def disable_administration(administration_id):
    connection = None

    try:
        user_id = int(get_jwt_identity())

        connection = connect()
        cursor = connection.cursor()

        # BUSCAR USUARIO LOGADO
        user = get_user_by_id(cursor, user_id)

        if not user:
            return jsonify({"error": "Usuário não encontrado."}), 404

        # VERIFICA SE A ADMINISTRACAO EXISTE
        administration = fetch_medicine_administration_by_id(cursor, administration_id)

        if not administration:
            return jsonify({"error": "Administração não encontrada."}), 404

        # VERIFICA SE JA ESTA DESATIVADA
        if not administration["active"]:
            return jsonify({"error": "Esta administração já está desativada."}), 400

        # CUIDADOR SÓ PODE DESATIVAR O QUE ELE MESMO REGISTROU
        if (
            user["role"].lower() == "caregiver"
            and administration["created_by_user_id"] != user_id
        ):
            return jsonify(
                {
                    "error": "Cuidador não pode desativar a administração registrada por outro cuidador."
                }
            ), 403

        set_medicine_administration_inactive(cursor, administration_id)

        connection.commit()

        return jsonify(
            {
                "message": "Administração desativada com sucesso.",
                "administration": {
                    "id": administration["id"],
                    "medicine_id": administration["medicine_id"],
                    "patient_id": administration["patient_id"],
                    "created_by_user_id": administration["created_by_user_id"],
                    "schedule_time": administration["schedule_time"],
                    "dosage_given": administration["dosage_given"],
                    "notes": administration["notes"],
                    "active": False,
                },
            }
        ), 200

    except Exception as e:
        if connection:
            connection.rollback()

        return jsonify({"error": str(e)}), 500

    finally:
        if connection:
            connection.close()

@administration_medications_bp.route(
    "/<int:patient_id>", methods=["GET"]
)
@jwt_required()
@roles_required("admin")
def admin_patient_history(patient_id):
    connection = None

    try:
        connection = connect()
        cursor = connection.cursor()

        administrations = fetch_medicine_administrations_by_patient(cursor, patient_id)

        if not administrations:
            return jsonify(
                {
                    "message": "Este paciente não possui registros de administrações.",
                    "administrations": [],
                }
            ), 200

        result = []

        for administration in administrations:
            result.append(
                {
                    "id": administration["id"],
                    "patient": {
                        "id": administration["patient_id"],
                        "name": administration["patient_name"],
                    },
                    "medicine": {
                        "id": administration["medicine_id"],
                        "name": administration["medicine_name"],
                    },
                    "schedule_time": administration["schedule_time"],
                    "administration_time": administration["administration_time"],
                    "administration_date": administration["administration_date"],
                    "dosage_given": administration["dosage_given"],
                    "notes": administration["notes"],
                    "active": administration["active"],
                    "created_by_user": {
                        "id": administration["created_by_user_id"],
                        "name": administration["created_by_user_name"],
                        "role": administration["created_by_user_role"],
                    },
                }
            )

        return jsonify({"administrations": result}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if connection:
            connection.close()


# CUIDADOR CONSULTA O HISTORICO DE UM PACIENTE VINCULADO
@administration_medications_bp.route(
    "/patient_history/<int:patient_id>", methods=["GET"]
)
@jwt_required()
@roles_required("caregiver")
def caregiver_patient_history(patient_id):
    connection = None

    try:
        caregiver_id = int(get_jwt_identity())

        connection = connect()
        cursor = connection.cursor()

        administrations = fetch_medicine_administrations_by_patient(cursor, caregiver_id, patient_id)

        if not administrations:
            return jsonify({"administrations": []}), 200

        result = []

        for administration in administrations:
            result.append(
                {
                    "id": administration["id"],
                    "patient": {
                        "id": administration["patient_id"],
                        "name": administration["patient_name"],
                    },
                    "medicine": {
                        "id": administration["medicine_id"],
                        "name": administration["medicine_name"],
                    },
                    "schedule_time": administration["schedule_time"],
                    "administration_time": administration["administration_time"],
                    "administration_date": administration["administration_date"],
                    "dosage_given": administration["dosage_given"],
                    "notes": administration["notes"],
                    "active": administration["active"],
                    "created_by_user": {
                        "id": administration["created_by_user_id"],
                        "name": administration["created_by_user_name"],
                        "role": administration["created_by_user_role"],
                    },
                }
            )

        return jsonify({"administrations": result}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if connection:
            connection.close()
