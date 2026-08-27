from flask import Blueprint, jsonify, request
from database.connect import connect
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.permissoes import admin_required, roles_required

administracao_medicamentos_bp = Blueprint("administracao_medicamentos", __name__)

#CRIA O REGISTRO DA ADMINISTRACAO DO MEDICAMENTO
@administracao_medicamentos_bp.route("/administracao_medicamentos/criar", methods=['POST'])
@jwt_required() 
@roles_required("admin", "cuidador")
def registrar_administracao():

    conexao = None

    try:
        dados = request.get_json()

        if not dados:
            return jsonify({
                "erro": "Dados não encontrados."
            }), 400

        #CAMPOS OBRIGATÓRIOS 
        if(
            "medicamento_id" not in dados
            or "paciente_id" not in dados
            or "status" not in dados
            or "horario_administrado" not in dados
            or "dosagem_administrada" not in dados
            or "obs" not in dados
        ):
            return jsonify({
                "erro": (
                    "medicamento_id, paciente_id, status, horario_administrado, "
                    "dosagem_administrada e obs são obrigatórios."
                    )
            }), 400

        #PEGA O ID DO USUÁRIO LOGADO
        usuario_id = get_jwt_identity()

        conexao = connect()
        cursor = conexao.cursor()

        #VERIFICA QUEM ESTÁ LOGADO
        cursor.execute("""
            SELECT id, nome, role
            FROM usuarios
            WHERE id = ?
        """, (usuario_id,))

        usuario = cursor.fetchone()

        if not usuario:
            return jsonify({
                "erro": "Usuário não encontrado."
            }), 404

        #VERIFICA SE QUEM ESTÁ LOGADO É ADMIN OU CUIDADOR
        if usuario["role"].lower() not in ["admin", "cuidador"]:
            return jsonify({
                "erro": "Usuário sem permissão para registrar administração."
            }), 403

        #VERIFICA SE O MEDICAMENTO EXISTE 
        cursor.execute("""
            SELECT id, paciente_id, nome
            FROM medicamentos
            WHERE id = ?
        """, (
            dados["medicamento_id"],
        ))

        medicamento = cursor.fetchone()

        if not medicamento:
            return jsonify({
                "erro": "Medicamento não encontrado."
            }), 404

        #VERIFICA SE O MEDICAMENTO PERTENCE AO PACIENTE 
        if medicamento["paciente_id"] != dados["paciente_id"]:
            return jsonify({
                "erro": "Este medicamento não pertence ao paciente informado."
            }), 400

        #VERIFICA SE O CUIDADOR ESTÁ VINCULADO AO PACIENTE
        if usuario["role"].lower() == "cuidador":

            cursor.execute("""
                SELECT id
                FROM cuidadores_pacientes
                WHERE cuidador_id = ?
                AND paciente_id = ?
            """, (
                usuario_id,
                dados["paciente_id"]
            ))

            vinculo = cursor.fetchone()

            if not vinculo:
                return jsonify({
                    "erro": "Cuidador não está vinculado a este paciente."
                }), 403

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
            dados["medicamento_id"],
            dados["paciente_id"],
            usuario_id,
            dados.get("horario_previsto"),
            dados["horario_administrado"],
            dados["dosagem_administrada"],
            dados["status"],
            dados["obs"]
        ))

        conexao.commit()
        return jsonify({
            "msg": "Administração registrada com sucesso.",

            "administração": {
                "id": cursor.lastrowid,
                "dosagem_administrada": dados["dosagem_administrada"],
                "horario_administrado": dados["horario_administrado"],
                "obs": dados["obs"]
            },

            "medicamento": {
                "id": medicamento["id"],
                "nome": medicamento["nome"]
            },

            "paciente_id": dados["paciente_id"],

            "responsavel": {
                "id": usuario["id"],
                "nome": usuario["nome"],
                "role": usuario["role"]
            },

            "status": dados["status"]
        }), 201

    except Exception as e:
        if conexao:
            conexao.rollback()

        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if conexao:
            conexao.close()

#LISTAR TODOS AS ADMINISTRAÇÕES
@administracao_medicamentos_bp.route("/administracao_medicamentos", methods= ['GET'])
@jwt_required()
@admin_required()
def listar_administracores():

    conexao = None

    try:
        conexao = connect()
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT 
                am.id,
                am.paciente_id,
                am.medicamento_id,
                am.dosagem_administrada,
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

        administracoes = cursor.fetchall()

        lista = []

        for administracao in administracoes:
            lista.append({
                "id": administracao["id"],

                "paciente": {
                    "id": administracao["paciente_id"],
                    "nome": administracao["paciente_nome"]
                },


                "medicamento": {
                    "id": administracao["medicamento_id"],
                    "nome": administracao["medicamento_nome"]
                },

                "dosagem_administrada": administracao["dosagem_administrada"],
                "horario_administrado": administracao["horario_administrado"],
                "obs": administracao["obs"],
                "status": administracao["status"],

                "responsavel": {
                    "nome": administracao["responsavel_nome"],
                    "role": administracao["responsavel_role"]
                }
            })

        return jsonify({
            "administracoes": lista
        }), 200

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if conexao:
            conexao.close()

# LISTA ADMINISTRACOES POR PACIENTE
@administracao_medicamentos_bp.route("/administracao_medicamentos/paciente/<int:paciente_id>", methods=['GET'])
@jwt_required()
@roles_required("admin", "cuidador")
def listar_administracoes_paciente(paciente_id):
    conexao = None

    try:
        usuario_id = get_jwt_identity()      

        conexao = connect()
        cursor = conexao.cursor()

        #BUSCA USUÁRIO LOGADO
        cursor.execute("""
            SELECT id, nome, role
            FROM usuarios
            WHERE id = ?
        """, (usuario_id,))

        usuario = cursor.fetchone()

        if not usuario:
            return jsonify({
                "erro": "Usuário não encontrado."
            }), 404

        #VERIFICA SE O PACIENTE EXISTE
        cursor.execute("""
            SELECT id, nome
            FROM usuarios
            WHERE id = ?
            AND role = 'paciente'
        """, (paciente_id,))

        paciente = cursor.fetchone()

        if not paciente:
             return jsonify({
                 "erro": "Paciente não encontrado."
             }), 404

        #SE FOR CUIDADOR, VERIFICA SE ESTA VINCULADO AO PACIENTE
        if usuario["role"].lower() == "cuidador":

            cursor.execute("""
                SELECT id
                FROM cuidadores_pacientes
                WHERE cuidador_id = ?
                AND paciente_id = ?
            """, (
                usuario_id,
                paciente_id
            ))

            vinculo = cursor.fetchone()

            if not vinculo:
                return jsonify({
                    "erro": "Cuidador não está vinculado a este paciente."
                }), 403

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
        """,(paciente_id,))

        administracoes = cursor.fetchall()

        if not administracoes:
            return jsonify({
                "msg": "Este paciente não possui registros de administação."
            }), 200

        lista = []

        for administracao in administracoes:
            lista.append({
                "id": administracao["id"],

                "medicamento": {
                    "id": administracao["medicamento_id"],
                    "nome": administracao["medicamento_nome"]
                },

                "horario_previsto": administracao["horario_previsto"],
                "horario_administrado": administracao["horario_administrado"],
                "dosagem_administrada": administracao["dosagem_administrada"],
                "obs": administracao["obs"],
                "status": administracao["status"],

                "responsavel": {
                    "id": administracao["responsavel_id"],
                    "nome": administracao["responsavel_nome"],
                    "role": administracao["responsavel_role"]
                }
            })

        return jsonify({
            "paciente": {
                "id": paciente["id"],
                "nome": paciente["nome"]
            },

            "administracoes": lista
        }), 200

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500


    finally:
        if conexao:
            conexao.close()