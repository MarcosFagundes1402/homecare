from flask import Blueprint, jsonify, request
from database.connect import connect
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from utils import (
    roles_required,
    buscar_usuario_por_id,
    buscar_role,
    erro_role,
    vinculo_cp,
    validate_required_fields,
    validate_non_empty_fields
    )

daily_reports_bp = Blueprint("relatorios_diarios", __name__)

@daily_reports_bp.route("/relatorios_diarios/criar", methods=['POST'])
@jwt_required()
@roles_required("admin", "cuidador")
def create_daily_reports():
    connection = None

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "erro": "Dados não encontrados."                
            }), 400

        # CAMPOS OBRIGATÓRIOS
        required_fields = [
            "paciente_id",
            "higiene",
            "observacoes"
        ]

        error = validate_required_fields(data, required_fields)

        if error:
            return jsonify({
                "erro": error
            }), 400
            
        user_id = int(get_jwt_identity())

        connection = connect()
        cursor = connection.cursor()

        #BUSCAR O USUARIO LOGADO
        user = buscar_usuario_por_id(cursor, user_id)

        if not user:
            return jsonify({
                "erro": "Usuário não encontrado."
            }), 404

        #VERIFICA SE O PACIENTE EXISTE
        patient, error, role_name = buscar_role(cursor, data["paciente_id"], "paciente")

        if error:
            return erro_role(error, role_name, patient)

        #SE FOR CUIDADOR, VERIFICA SE ESTÁ VINCULADO AO PACIENTE
        if user["role"].lower() == "cuidador":
            existing_link = vinculo_cp(cursor, user_id, data["paciente_id"])

            if not existing_link:
                return jsonify({
                    "erro": "Cuidador não está vinculado a este paciente."
                }), 403

        #ADICIONAR A TABELA O RELATORIO
        data_horario = datetime.now().strftime("%d/%m/%Y | %H:%M:%S")

        cursor.execute("""
            INSERT INTO relatorios_diarios(
                paciente_id,
                responsavel_id,
                alimentacao,
                higiene,
                pressao_arterial,
                glicemia,
                temperatura,
                observacoes,
                data_horario
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["paciente_id"],
            user_id,
            data.get("alimentacao"),
            data.get("higiene"),
            str(data.get("pressao_arterial", "")).strip() or "não aferido",
            str(data.get("glicemia", "")).strip() or "não aferido",
            str(data.get("temperatura", "")).strip() or "não aferido",
            data.get("observacoes"),
            data_horario
        ))

        connection.commit()

        return jsonify({
            "msg": "Relatório diário criado com sucesso.",

            "relatorio": {
                "id": cursor.lastrowid,
                "paciente_id": data["paciente_id"],
                "responsavel_id": user_id,
                "alimentacao": data.get("alimentacao"),
                "higiene": data.get("higiene"),
                "pressao_arterial": str(data.get("pressao_arterial", "")).strip() or "não aferido",
                "glicemia": str(data.get("glicemia", "")).strip() or "não aferido",
                "temperatura": str(data.get("temperatura", "")).strip() or "não aferido",
                "observacoes": data.get("observacoes"),
                "data_horario": data_horario
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

#LISTAR RELATÓRIOS DIÁRIOS POR PACIENTE
@daily_reports_bp.route("/relatorios_diarios/paciente/<int:patient_id>", methods=['GET'])
@jwt_required()
@roles_required("admin", "cuidador")
def get_patient_daily_reports(patient_id):
    connection = None

    try:
        user_id = int(get_jwt_identity())

        connection = connect()
        cursor = connection.cursor()

        #BUSCAR USUARIO LOGADO
        user = buscar_usuario_por_id(cursor, user_id)

        if not user:
            return jsonify({
                "erro": "Usuário não encontrado."
            }), 404

        #VERIFICA SE O PACIENTE EXISTE
        patient, error, role_name = buscar_role(cursor, patient_id, "paciente")

        if error:
            return erro_role(error, role_name, patient)

        #VERIFICA VINCULO ENTRE CUIDADOR E PACIENTE
        if user["role"].lower() == "cuidador":
            existing_link = vinculo_cp(cursor, user_id, patient_id) 

            if not existing_link:
                return jsonify({
                    "erro": "Cuidador não está vinculado a este paciente."
                }), 403

        #BUSCA RELATORIOS
        cursor.execute("""
            SELECT
                rd.id,
                rd.alimentacao,
                rd.higiene,
                rd.pressao_arterial,
                rd.glicemia,
                rd.temperatura,
                rd.observacoes,
                rd.data_horario,

                u.id AS responsavel_id,
                u.nome AS responsavel_nome,
                u.role AS responsavel_role

            FROM relatorios_diarios rd

            JOIN usuarios u
                ON u.id = rd.responsavel_id
            
            WHERE rd.paciente_id = ?

            ORDER BY rd.id DESC
        """, (patient_id,))

        daily_reports = cursor.fetchall()

        if not daily_reports:
            return jsonify({
                "paciente": {
                    "id": patient["id"],
                    "nome": patient["nome"]
                },
                "relatorios": []
            }), 200

        report_list = []

        for daily_report in daily_reports:
            report_list.append({
                "id": daily_report["id"],
                "alimentacao": daily_report["alimentacao"],
                "higiene": daily_report["higiene"],
                "pressao_arterial": daily_report["pressao_arterial"],
                "glicemia": daily_report["glicemia"],
                "temperatura": daily_report["temperatura"],
                "observacoes": daily_report["observacoes"],
                "data_horario": daily_report["data_horario"],

                "responsavel": {
                    "id": daily_report["responsavel_id"],
                    "nome": daily_report["responsavel_nome"],
                    "role": daily_report["responsavel_role"]
                }
            })

        return jsonify({
            "paciente": {
                "id": patient["id"],
                "nome": patient["nome"]
            },

            "relatorios": report_list
        }), 200

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if connection:
             connection.close()

# LISTAR TODOS OS RELATORIOS DIARIOS
@daily_reports_bp.route("/relatorios_diarios", methods=['GET'])
@jwt_required()
@roles_required("admin")
def get_daily_reports():
    connection = None

    try:
        connection = connect()
        cursor = connection.cursor()

        #BUSCA TODOS OS RELATORIOS
        cursor.execute("""
            SELECT 
                rd.id,
                rd.paciente_id,
                rd.responsavel_id,
                rd.alimentacao,
                rd.higiene,
                rd.pressao_arterial,
                rd.glicemia,
                rd.temperatura,
                rd.observacoes,
                rd.data_horario,

                p.nome AS paciente_nome,

                r.nome AS responsavel_nome,
                r.role AS responsavel_role

            FROM relatorios_diarios rd

            JOIN usuarios p
                ON p.id = rd.paciente_id
            
            JOIN usuarios r
                ON r.id = rd.responsavel_id

            ORDER BY rd.id DESC
        """)

        daily_reports = cursor.fetchall()

        if not daily_reports:
            return jsonify({
                "relatorios": []
            }), 200

        report_list = []

        for daily_report in daily_reports:
            report_list.append({
                "id": daily_report["id"],

                "paciente": {
                    "id": daily_report["paciente_id"],
                    "nome": daily_report["paciente_nome"]
                },

                "alimentacao": daily_report["alimentacao"],
                "higiene": daily_report["higiene"],
                "pressao_arterial": daily_report["pressao_arterial"],
                "glicemia": daily_report["glicemia"],
                "temperatura": daily_report["temperatura"],
                "observacoes": daily_report["observacoes"],
                "data_horario": daily_report["data_horario"],

                "responsavel": {
                    "id": daily_report["responsavel_id"],
                    "nome": daily_report["responsavel_nome"],
                    "role": daily_report["responsavel_role"]
                }
            })

        return jsonify({
            "relatorios": report_list
        }), 200

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if connection:
            connection.close()

#EDITAR RELATORIO DIARIO
@daily_reports_bp.route("/relatorios_diarios/editar/<int:id>", methods=['PATCH'])
@jwt_required()
@roles_required("admin", "cuidador")
def edit_daily_report(report_id):
    connection = None

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "erro": "Dados não econtrados."
            }), 400

        user_id = int(get_jwt_identity())

        connection = connect()
        cursor = connection.cursor()

        #BUSCA USUARIO LOGADO
        user = buscar_usuario_por_id(cursor, user_id)
 
        if not user:
            return jsonify({
                "erro": "Usuário não encontrado."
            }), 404

        #BUSCAR O RELATORIO
        cursor.execute("""
            SELECT
                id,
                paciente_id,
                responsavel_id,
                alimentacao,
                higiene,
                pressao_arterial,
                glicemia,
                temperatura,
                observacoes,
                data_horario
            FROM relatorios_diarios
            WHERE id = ?
        """, (report_id,))

        daily_report = cursor.fetchone()

        if not daily_report:
            return jsonify({
                "erro": "Relatório não encontrados."
            }), 404

        #CUIDADOR SO PODE EDITAR RELATORIO QUE ELE MESMO CRIOU
        if user["role"].lower() == "cuidador":

            if daily_report["responsavel_id"] != user_id:
                return jsonify({
                    "erro": "Cuidador não pode editar relatório criado por outro usuário."
                }), 403
            
            # VERIFICA SE AINDA POSSUI VÍNCULO COM O PACIENTE
            existing_link = vinculo_cp(cursor, user_id, daily_report["paciente_id"])

            if not existing_link:
                return jsonify({
                    "erro": "Cuidador não está vinculado a este paciente."
                }), 403


        #CAMPOS QUE PODER SER EDITADOS
        allowed_fields = [
            "alimentacao",
            "higiene",
            "pressao_arterial",
            "glicemia",
            "temperatura",
            "observacoes"
        ]

        for field in data:
            if field not in allowed_fields:
                return jsonify({
                    "erro": f"O campo '{field}' não pode ser editado."
                }), 400
            
        #CAMPOS QUE NAO PODE FICAR VAZIO
        non_empty_fields = [
            "higiene",
            "observacoes"
        ]

        error = validate_non_empty_fields(data, non_empty_fields)

        if error:
            return jsonify({
                "erro": error
            }), 400
            
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

        values.append(report_id)

        #ATUALIZA O RELATORIO
        cursor.execute(f"""
            UPDATE relatorios_diarios
            SET {", ".join(fields)}
            WHERE id = ?
        """, values)

        connection.commit()

        return jsonify({
            "msg": "Relatório atualizado com sucesso."
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

#DESATIVAR RELATORIOS DIARIO
@daily_reports_bp.route("/relatorios_diarios/desativar/<int:id>", methods=['DELETE'])
@jwt_required()
@roles_required("admin")
def disable_daily_report(report_id):
    connection = None

    try:
        connection = connect()
        cursor = connection.cursor()

        #VERIFICAR SE O RELATORIO EXISTE
        cursor.execute("""
            SELECT 
                id,
                paciente_id,
                responsavel_id,
                alimentacao,
                higiene,
                pressao_arterial,
                glicemia,
                temperatura,
                observacoes,
                data_horario,
                status
            FROM relatorios_diarios
            WHERE id = ?
        """,(report_id,))

        daily_report = cursor.fetchone()

        if not daily_report:
            return jsonify({
                "erro": "Relatório não encontrado."
            }), 404

        if daily_report["status"] == "inativo":
            return jsonify({
                "erro": "Este relatório já está inativo."
            }), 400

        #DESATIVA O RELATORIO
        cursor.execute("""
            UPDATE relatorios_diarios
            SET status = 'inativo'
            WHERE id = ?
        """, (report_id,))

        connection.commit()

        return jsonify({
            "msg": "Relatório desativado com sucesso.",

            "relatorio_desativado": {
                "id": daily_report["id"],
                "paciente_id": daily_report["paciente_id"],
                "responsavel_id": daily_report["responsavel_id"],
                "alimentacao": daily_report["alimentacao"],
                "higiene": daily_report["higiene"],
                "pressao_arterial": daily_report["pressao_arterial"],
                "glicemia": daily_report["glicemia"],
                "temperatura": daily_report["temperatura"],
                "observacoes": daily_report["observacoes"],
                "data_horario": daily_report["data_horario"],
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
