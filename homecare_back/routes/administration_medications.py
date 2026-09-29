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
    get_caregiver_patient_link,
    validate_user_role,
    )

administration_medications_bp = Blueprint("administracao_medicamentos", __name__)

#CRIA O REGISTRO DA ADMINISTRACAO DO MEDICAMENTO
@administration_medications_bp.route("/administracao_medicamentos/criar", methods=['POST'])
@jwt_required() 
@roles_required("admin", "cuidador")
def register_administration():

    connection = None

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "erro": "Dados não encontrados."
            }), 400

        #CAMPOS OBRIGATÓRIOS 
        required_fields = [
            "medicamento_id",
            "paciente_id",
            "dosagem_administrada",
        ]

        # VALIDA OS CAMPOS OBRIGATORIOS
        error = validate_required_fields(data, required_fields)

        if error:
            return jsonify({
                "erro": error
            }), 400

        #PEGA O ID DO USUÁRIO LOGADO
        user_id = int(get_jwt_identity())

        connection = connect()
        cursor = connection.cursor()

        #VERIFICA QUEM ESTÁ LOGADO
        user = get_user_by_id(cursor, user_id)

        if not user:
            return jsonify({
                "erro": "Usuário não encontrado."
            }), 404

        #VERIFICA SE O MEDICAMENTO EXISTE 
        cursor.execute("""
            SELECT id, paciente_id, nome
            FROM medicamentos
            WHERE id = ?
        """, (
            data["medicamento_id"],
        ))

        medicine = cursor.fetchone()

        if not medicine:
            return jsonify({
                "erro": "Medicamento não encontrado."
            }), 404

        #VERIFICA SE O MEDICAMENTO PERTENCE AO PACIENTE 
        if medicine["paciente_id"] != data["paciente_id"]:
            return jsonify({
                "erro": "Este medicamento não pertence ao paciente informado."
            }), 400

        #VERIFICA SE O CUIDADOR ESTÁ VINCULADO AO PACIENTE
        if user["role"].lower() == "cuidador":

            bond = get_caregiver_patient_link(cursor, user_id, data["paciente_id"])

            if not bond:
                return jsonify({
                    "erro": "Cuidador não está vinculado a este paciente."
                }), 403
            
        #VERIFICA SE JÁ EXISTE ADMINISTRACAO NO MESMO HORARIO
        administration_time = datetime.now().strftime("%d-%m-%Y | %H:%M")

        cursor.execute("""
            SELECT id
            FROM administracao_medicamentos
            WHERE medicamento_id = ?
            AND paciente_id = ?
            AND horario_administrado = ?
        """, (
            data["medicamento_id"],
            data["paciente_id"],
            administration_time,
        ))

        existing_administration = cursor.fetchone()

        if existing_administration:
            return jsonify({
                "erro": "Já existe uma administração deste medicamento no mesmo horário."
            }), 409

        status = data.get("status", "ativo")

        #REGISTRAR A ADMINISTRAÇÃO DO MEDICAMENTO
        cursor.execute("""
            INSERT INTO administracao_medicamentos(
                medicamento_id,
                paciente_id,
                responsavel_id,
                horario_previsto,
                horario_administrado,
                dosagem_administrada,
                status,
                obs                
            )
            VALUES(?, ?, ?, ?, ?, ?, ?, ?)
        """,(
            data["medicamento_id"],
            data["paciente_id"],
            user_id,
            data.get("horario_previsto"),
            administration_time,
            data["dosagem_administrada"],
            status,
            data.get("obs")
        ))

        administration_id = cursor.lastrowid

        connection.commit()

        return jsonify({
            "msg": "Administração registrada com sucesso.",

            "administração": {
                "id": administration_id,
                "dosagem_administrada": data["dosagem_administrada"],
                "horario_previsto": data.get("horario_previsto"),
                "horario_administrado": administration_time,
                "obs": data.get("obs")
            },

            "medicamento": {
                "id": medicine["id"],
                "nome": medicine["nome"]
            },

            "paciente_id": data["paciente_id"],

            "responsavel": {
                "id": user["id"],
                "nome": user["nome"],
                "role": user["role"]
            },

            "status": status
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

#LISTAR TODOS AS ADMINISTRAÇÕES
@administration_medications_bp.route("/administracao_medicamentos", methods= ['GET'])
@jwt_required()
@roles_required("admin")
def list_administrations():

    connection = None

    try:
        connection = connect()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT 
                am.id,
                am.paciente_id,
                am.medicamento_id,
                am.responsavel_id,
                am.dosagem_administrada,
                am.horario_previsto,
                am.horario_administrado,
                am.obs,
                am.status,

                m.nome AS medicamento_nome,
                u.nome AS paciente_nome,
                r.nome AS responsavel_nome,
                r.role AS responsavel_role

            FROM administracao_medicamentos am
            
            JOIN medicamentos m
                ON m.id = am.medicamento_id

            JOIN usuarios u
                ON u.id = am.paciente_id
            
            JOIN usuarios r
                ON r.id = am.responsavel_id

            ORDER BY am.id DESC
        """)

        administrations = cursor.fetchall()

        administration_list = []

        for administration in administrations:
            administration_list.append({
                "id": administration["id"],

                "paciente": {
                    "id": administration["paciente_id"],
                    "nome": administration["paciente_nome"]
                },


                "medicamento": {
                    "id": administration["medicamento_id"],
                    "nome": administration["medicamento_nome"]
                },

                "dosagem_administrada": administration["dosagem_administrada"],
                "horario_previsto": administration["horario_previsto"],
                "horario_administrado": administration["horario_administrado"],
                "obs": administration["obs"],
                "status": administration["status"],

                "responsavel": {
                    "id": administration["responsavel_id"],
                    "nome": administration["responsavel_nome"],
                    "role": administration["responsavel_role"]
                }
            })

        return jsonify({
            "administracoes": administration_list
        }), 200

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if connection:
            connection.close()

#PACIENTE CONSULTA O PROPRIO HISTORICO
@administration_medications_bp.route("/administracao_medicamentos/paciente/meu-historico", methods=['GET'])
@jwt_required()
@roles_required("paciente")
def my_history():
    connection = None

    try:
        patient_id = int(get_jwt_identity())      

        connection = connect()
        cursor = connection.cursor()

        #VALIDA O PACIENTE LOGADO
        patient, error, role_name = validate_user_role(cursor, patient_id, "paciente")

        if error:
            return error_role(error, role_name, patient)

        #BUSCAR AS ADMINISTRACOES DO PACIENTE
        cursor.execute("""
            SELECT 
                am.id,
                am.paciente_id,
                am.medicamento_id,
                am.horario_previsto,
                am.horario_administrado,
                am.dosagem_administrada,
                am.obs,
                am.status,

                m.nome AS medicamento_nome,

                r.id AS responsavel_id,
                r.nome AS responsavel_nome,
                r.role AS responsavel_role

            FROM administracao_medicamentos am

            JOIN medicamentos m
                ON m.id = am.medicamento_id

            JOIN usuarios r 
                ON r.id = am.responsavel_id

            WHERE am.paciente_id = ?
            
            ORDER BY am.id DESC
        """,(patient_id,))

        administrations = cursor.fetchall()

        if not administrations:
            return jsonify({
                "paciente": {
                    "id": patient["id"],
                    "nome": patient["nome"]
                },
                "administracoes": []
            }), 200

        result = []

        for administration in administrations:
            result.append({
                "id": administration["id"],

                "medicamento": {
                    "id": administration["medicamento_id"],
                    "nome": administration["medicamento_nome"]
                },

                "horario_previsto": administration["horario_previsto"],
                "horario_administrado": administration["horario_administrado"],
                "dosagem_administrada": administration["dosagem_administrada"],
                "obs": administration["obs"],
                "status": administration["status"],

                "responsavel": {
                    "id": administration["responsavel_id"],
                    "nome": administration["responsavel_nome"],
                    "role": administration["responsavel_role"]
                }
            })

        return jsonify({
            "paciente": {
                "id": patient["id"],
                "nome": patient["nome"]
            },

            "administracoes": result
        }), 200

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500


    finally:
        if connection:
            connection.close()

#CUIDADOR CONSULTA O HISTORICO DOS PROPRIOS PACIENTES
@administration_medications_bp.route("/administracao_medicamentos/cuidador/meus-pacientes", methods=['GET'])
@jwt_required()
@roles_required("cuidador")
def my_patients_history():
    connection = None

    try:
        caregiver_id = int(get_jwt_identity())

        connection = connect()
        cursor = connection.cursor()

        #BUSCA AS ADMINISTRACOES DOS PACIENTES VINCULADOS AO CUIDADOR
        cursor.execute("""
            SELECT 
                am.id,
                am.paciente_id,
                am.medicamento_id,
                am.horario_previsto,
                am.horario_administrado,
                am.dosagem_administrada,
                am.obs,
                am.status,

                p.nome AS paciente_nome,

                m.nome AS medicamento_nome,
                
                u.id AS responsavel_id,
                u.nome AS responsavel_nome,
                u.role AS responsavel_role
            FROM  administracao_medicamentos am

            JOIN cuidadores_pacientes cp
                ON cp.paciente_id = am.paciente_id
            
            JOIN usuarios p
                ON p.id = am.paciente_id

            JOIN medicamentos m
                ON m.id = am.medicamento_id
            
            JOIN usuarios u
                ON u.id = am.responsavel_id
            
            WHERE cp.cuidador_id = ?

            ORDER BY am.id DESC
        """, (caregiver_id,))

        administrations = cursor.fetchall()

        if not administrations:
            return jsonify({
                "adminstracoes": []
            }), 200

        result = []

        for administration in administrations:
            result.append({
                "id": administration["id"],

                "paciente": {
                    "id": administration["paciente_id"],
                    "nome": administration["paciente_nome"]
                },

                "medicamento": {
                    "id": administration["medicamento_id"],
                    "nome": administration["medicamento_nome"]
                },

                "horario_previsto": administration["horario_previsto"],
                "horario_administrado":administration["horario_administrado"],
                "dosagem_administrada": administration["dosagem_administrada"],
                "obs": administration["obs"],
                "status": administration["status"],

                "responsavel": {
                    "id": administration["responsavel_id"],
                    "nome": administration["responsavel_nome"],
                    "role": administration["responsavel_role"]
                }
            })

        return jsonify({
            "administracoes": result
        }), 200

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }),  500

    finally:
        if connection:
            connection.close()

#EDITAR ADMINISTRACAO DE MEDICAMENTOS
@administration_medications_bp.route("/administracao_medicamentos/editar/<int:id>", methods=['PATCH'])
@jwt_required()
@roles_required("admin", "cuidador")
def edit_administration(administration_id):
    connection = None

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "erro": "Dados não encontrados."
            }), 400

        user_id = int(get_jwt_identity())

        connection = connect()
        cursor = connection.cursor()

        #BUSCA O USUARIO LOGADO
        user = get_user_by_id(cursor, user_id)

        if not user:
            return jsonify({
                "erro": "Usuário não encontrado."
            }), 404

        #BUSCA A ADMINISTRACAO
        cursor.execute("""
            SELECT
                id,
                paciente_id,
                medicamento_id,
                responsavel_id,
                horario_administrado,
                dosagem_administrada,
                status,
                obs
            FROM administracao_medicamentos
            WHERE id = ?
        """, (administration_id,))

        administration = cursor.fetchone()

        if not administration:
            return jsonify ({
                "erro": "Administração não encontrada."
            }), 404

        #SE FOR CUIDADOR, SÓ PODE EDITAR O QUE ELE MESMO REGISTROU
        if user["role"].lower() == "cuidador":
            if administration["responsavel_id"] != user_id:
                return jsonify({
                    "erro": "Cuidador não pode editar administração registrada por outro cuidador."
                }), 403

        #CAMPOS QUE PODEM SER EDITADOS
        required_fields = [
            "dosagem_administrada",
            "status",
            "obs"
        ]

        #VERIFICA SE FOI ENVIADO ALGUM CAMPO NAO PERMITIDO
        error = validate_required_fields(data, required_fields)

        if error:
            return jsonify({
                "erro": error
            }), 400

        allowed_fields = [
            "dosagem_administrada",
            "status"
        ]

        error = validate_non_empty_fields(data, allowed_fields)

        if error:
            return jsonify({
                "erro": error
            }), 400

        fields = []
        values = []

        for field in required_fields:
            if field in data:
                fields.append(f"{field} = ?")
                values.append(data[field])

        if not fields:
             return jsonify({
                 "erro": "Nenhum campo válido foi enviado para edição."
             }), 400

        values.append(administration_id)

        #ATUALIZA A ADMINISTRACAO
        cursor.execute(f"""  
            UPDATE administracao_medicamentos
            SET {", ".join(fields)}
            WHERE id = ?
        """, values)

        connection.commit()

        return jsonify({
            "msg": "Administração atualizada com sucesso.",
            "administracao": administration_id,
            "campos_atualizados": data
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

#DESATIVAR REGISTRO DE ADMINISTRACAO
@administration_medications_bp.route("/administracao_medicamentos/desativar/<int:id>", methods=['DELETE'])
@jwt_required()
@roles_required("admin", "cuidador")
def disable_administration(administration_id):
    connection = None

    try:
        user_id = int(get_jwt_identity())

        connection = connect()
        cursor = connection.cursor()

        #BUSCAR USUARIO LOGADO
        user = get_user_by_id(cursor, user_id)

        if not user:
            return jsonify({
                "erro": "Usuário não encontrado."
            }), 404

        #VERIFICA SE A ADMINISTRACAO EXISTE
        cursor.execute("""
            SELECT
                id,
                medicamento_id,
                paciente_id,
                responsavel_id,
                horario_administrado,
                dosagem_administrada,
                status,
                obs
            FROM administracao_medicamentos
            WHERE id = ?
        """, (administration_id,))

        administration = cursor.fetchone()

        if not administration:
             return jsonify({
                 "erro": "Administração não encontrada."
             }), 404

        #VERIFICA SE JA ESTA DESATIVADA
        if administration["status"] == "inativo":
            return jsonify({
                "erro": "Esta administração já está desativada."
                }), 400

        # CUIDADOR SÓ PODE DESATIVAR O QUE ELE MESMO REGISTROU
        if user["role"].lower() == "cuidador":
            if administration["responsavel_id"] != user_id:
                return jsonify({
                    "erro": "Cuidador não pode desativar a administração registrada por outro cuidador."
                }), 403

        #DESATIVA A ADMINISTRACAO
        cursor.execute("""
            UPDATE administracao_medicamentos
            SET status = 'inativo'
            WHERE id = ?
        """, (administration_id,))

        connection.commit()

        return jsonify({
            "msg": "Administração desativada com sucesso.",

            "administracao": {
                "id": administration["id"],
                "medicamento_id": administration["medicamento_id"],
                "paciente_id": administration["paciente_id"],
                "responsavel_id": administration["responsavel_id"],
                "horario_administrado": administration["horario_administrado"],
                "dosagem_administrada": administration["dosagem_administrada"],
                "status": "inativo",
                "obs": administration["obs"]
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


@administration_medications_bp.route("/administracao_medicamentos/admin/paciente/<int:patient_id>", methods=["GET"])
@jwt_required()
@roles_required("admin")
def admin_patient_history(patient_id):
    connection = None

    try:
        connection = connect()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                am.id,
                am.paciente_id,
                am.medicamento_id,
                am.horario_previsto,
                am.horario_administrado,
                am.dosagem_administrada,
                am.obs,
                am.status,

                p.nome AS paciente_nome,
                m.nome AS medicamento_nome,

                u.id AS responsavel_id,
                u.nome AS responsavel_nome,
                u.role AS responsavel_role

            FROM administracao_medicamentos am

            JOIN usuarios p
                ON p.id = am.paciente_id

            JOIN medicamentos m
                ON m.id = am.medicamento_id

            JOIN usuarios u
                ON u.id = am.responsavel_id

            WHERE am.paciente_id = ?

            ORDER BY am.id DESC
        """, (patient_id,))

        administrarions = cursor.fetchall()

        if not administrarions:
            return jsonify({
                "msg": "Este paciente não possui registros de administrações.",
                "administracoes": []
            }), 200

        result = []

        for administration in administrarions:
            result.append({
                "id": administration["id"],

                "paciente": {
                    "id": administration["paciente_id"],
                    "nome": administration["paciente_nome"]
                },

                "medicamento": {
                    "id": administration["medicamento_id"],
                    "nome": administration["medicamento_nome"]
                },

                "horario_previsto": administration["horario_previsto"],
                "horario_administrado": administration["horario_administrado"],
                "dosagem_administrada": administration["dosagem_administrada"],
                "obs": administration["obs"],
                "status": administration["status"],

                "responsavel": {
                    "id": administration["responsavel_id"],
                    "nome": administration["responsavel_nome"],
                    "role": administration["responsavel_role"]
                }
            })

        return jsonify({
            "administracoes": result
        }), 200

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if connection:
            connection.close()

#CUIDADOR CONSULTA O HISTORICO DE UM PACIENTE VINCULADO
@administration_medications_bp.route("/administracao_medicamentos/cuidador/paciente/<int:paciente_id>", methods=['GET'])
@jwt_required()
@roles_required("cuidador")
def caregiver_patient_history(patient_id):
    connection = None

    try:
        caregiver_id = int(get_jwt_identity())

        connection = connect()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT 
                am.id,
                am.paciente_id,
                am.medicamento_id,
                am.horario_previsto,
                am.horario_administrado,
                am.dosagem_administrada,
                am.obs,
                am.status,

                p.nome AS paciente_nome,
                m.nome AS medicamento_nome,
                u.id AS responsavel_id,
                u.nome AS responsavel_nome,
                u.role AS responsavel_role
            
            FROM administracao_medicamentos am

            JOIN cuidadores_pacientes cp
                ON cp.paciente_id = am.paciente_id
            
            JOIN usuarios p
                ON p.id = am.paciente_id
            
            JOIN medicamentos m
                ON m.id = am.medicamento_id
            
            JOIN usuarios u
                ON u.id = am.responsavel_id
            
            WHERE cp.cuidador_id = ?
            AND am.paciente_id = ?

            ORDER BY am.id DESC
        """, (
            caregiver_id,
            patient_id
        ))

        administrations = cursor.fetchall()

        if not administrations:
            return jsonify({
                "administracoes": []
            }), 200

        result = []

        for administration in administrations:
            result.append({
                "id": administration["id"],

                "paciente": {
                    "id": administration["paciente_id"],
                    "nome": administration["paciente_nome"]
                },

                "medicamento": {
                    "id": administration["medicamento_id"],
                    "nome": administration["medicamento_nome"]
                },

                "horario_previsto": administration["horario_previsto"],
                "horario_administrado": administration["horario_administrado"],
                "dosagem_administrada": administration["dosagem_administrada"],
                "obs": administration["obs"],
                "status": administration["status"],

                "responsavel": {
                    "id": administration["responsavel_id"],
                    "nome": administration["responsavel_nome"],
                    "role": administration["responsavel_role"],
                }
            })

        return jsonify({
            "administracoes": result
        }), 200

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if connection:
            connection.close()