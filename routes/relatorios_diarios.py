from flask import Blueprint, jsonify, request
from database.connect import connect
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from utils import (
    roles_required,
    buscar_usuario_por_id,
    buscar_role,
    erro_role,
    vinculo_cp
    )

relatorios_diarios_bp = Blueprint("relatorios_diarios", __name__)

@relatorios_diarios_bp.route("/relatorios_diarios/criar", methods=['POST'])
@jwt_required()
@roles_required("admin", "cuidador")
def criar_relatorio():
    conexao = None

    try:
        dados = request.get_json()

        if not dados:
            return jsonify({
                "erro": "Dados não encontrados."                
            }), 400

        #CAMPOS OBRIGATORIOS
        if "paciente_id" not in dados:
            return jsonify({
                "erro": "paciente_id é obrigatório."
            }), 400

        usuario_id = int(get_jwt_identity())

        conexao = connect()
        cursor = conexao.cursor()

        #BUSCAR O USUARIO LOGADO
        usuario = buscar_usuario_por_id(cursor, usuario_id)

        if not usuario:
            return jsonify({
                "erro": "Usuário não encontrado."
            }), 404

        #VERIFICA SE O PACIENTE EXISTE
        paciente, erro, role_nome = buscar_role(cursor, dados["paciente_id"], "paciente")

        if erro:
            return erro_role(erro, role_nome, paciente)

        #SE FOR CUIDADOR, VERIFICA SE ESTÁ VINCULADO AO PACIENTE
        if usuario["role"].lower() == "cuidador":
            vinculo = vinculo_cp(cursor, usuario_id, dados["paciente_id"])

            if not vinculo:
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
            dados["paciente_id"],
            usuario_id,
            dados.get("alimentacao"),
            dados.get("higiene"),
            dados.get("pressao_arterial"),
            dados.get("glicemia"),
            dados.get("temperatura"),
            dados.get("observacoes"),
            data_horario
        ))

        conexao.commit()

        return jsonify({
            "msg": "Relatório diário criado com sucesso.",

            "relatorio": {
                "id": cursor.lastrowid,
                "paciente_id": dados["paciente_id"],
                "responsavel_id": usuario_id,
                "alimentacao": dados.get("alimentacao"),
                "higiene": dados.get("higiene"),
                "pressao_arterial": dados.get("pressao_arterial"),
                "glicemia": dados.get("glicemia"),
                "temperatura": dados.get("temperatura"),
                "observacoes": dados.get("observacoes"),
                "data_horario": data_horario
            }
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

#LISTAR RELATÓRIOS DIÁRIOS POR PACIENTE
@relatorios_diarios_bp.route("/relatorios_diarios/paciente/<int:paciente_id>", methods=['GET'])
@jwt_required()
@roles_required("admin", "cuidador")
def listar_relatorios_paciente(paciente_id):
    conexao = None

    try:
        usuario_id = int(get_jwt_identity())

        conexao = connect()
        cursor = conexao.cursor()

        #BUSCAR USUARIO LOGADO
        usuario = buscar_usuario_por_id(cursor, usuario_id)

        if not usuario:
            return jsonify({
                "erro": "Usuário não encontrado."
            }), 404

        #VERIFICA SE O PACIENTE EXISTE
        paciente, erro, role_nome = buscar_role(cursor, paciente_id, "paciente")

        if erro:
            return erro_role(erro, role_nome, paciente)

        #VERIFICA VINCULO ENTRE CUIDADOR E PACIENTE
        if usuario["role"].lower() == "cuidador":
            vinculo = vinculo_cp(cursor, usuario_id, paciente_id) 

            if not vinculo:
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
        """, (paciente_id,))

        relatorios = cursor.fetchall()

        if not relatorios:
            return jsonify({
                "msg": "Este paciente não possui relatórios cadastrados."
            }), 200

        lista = []

        for relatorio in relatorios:
            lista.append({
                "id": relatorio["id"],
                "alimentacao": relatorio["alimentacao"],
                "higiene": relatorio["higiene"],
                "pressao_arterial": relatorio["pressao_arterial"],
                "glicemia": relatorio["glicemia"],
                "temperatura": relatorio["temperatura"],
                "observacoes": relatorio["observacoes"],
                "data_horario": relatorio["data_horario"],

                "responsavel": {
                    "id": relatorio["responsavel_id"],
                    "nome": relatorio["responsavel_nome"],
                    "role": relatorio["responsavel_role"]
                }
            })

        return jsonify({
            "paciente": {
                "id": paciente["id"],
                "nome": paciente["nome"]
            },

            "relatorios": lista
        }), 200

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if conexao:
             conexao.close()

# LISTAR TODOS OS RELATORIOS DIARIOS
@relatorios_diarios_bp.route("/relatorios_diarios", methods=['GET'])
@jwt_required()
@roles_required("admin")
def listar_relatorios():
    conexao = None

    try:
        conexao = connect()
        cursor = conexao.cursor()

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

        relatorios = cursor.fetchall()

        if not relatorios:
            return jsonify({
                "msg": "Nenhum relatório cadastrado."
            }), 200

        lista = []

        for relatorio in relatorios:
            lista.append({
                "id": relatorio["id"],

                "paciente": {
                    "id": relatorio["paciente_id"],
                    "nome": relatorio["paciente_nome"]
                },

                "alimentacao": relatorio["alimentacao"],
                "higiene": relatorio["higiene"],
                "pressao_arterial": relatorio["pressao_arterial"],
                "glicemia": relatorio["glicemia"],
                "temperatura": relatorio["temperatura"],
                "observacoes": relatorio["observacoes"],
                "data_horario": relatorio["data_horario"],

                "responsavel": {
                    "id": relatorio["responsavel_id"],
                    "nome": relatorio["responsavel_nome"],
                    "role": relatorio["responsavel_role"]
                }
            })

        return jsonify({
            "relatorios": lista
        }), 200

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if conexao:
            conexao.close()

#EDITAR RELATORIO DIARIO
@relatorios_diarios_bp.route("/relatorios_diarios/editar/<int:id>", methods=['PATCH'])
@jwt_required()
@roles_required("admin", "cuidador")
def editar_relatorios(id):
    conexao = None

    try:
        dados = request.get_json()

        if not dados:
            return jsonify({
                "erro": "Dados não econtrado."
            }), 400

        usuario_id = int(get_jwt_identity())

        conexao = connect()
        cursor = conexao.cursor()

        #BUSCA USUARIO LOGADO
        usuario = buscar_usuario_por_id(cursor, usuario_id)
 
        if not usuario:
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
        """, (id,))

        relatorio = cursor.fetchone()

        if not relatorio:
            return jsonify({
                "erro": "Relatório não encontrado."
            }), 404

        #CUIDADOR SO PODE EDITAR RELATORIO QUE ELE MESMO CRIOU
        if usuario["role"].lower() == "cuidador":

            if relatorio["responsavel_id"] != usuario_id:
                return jsonify({
                    "erro": "Cuidador não pode editar relatório criado por outro usuário."
                }), 403
            
            # VERIFICA SE AINDA POSSUI VÍNCULO COM O PACIENTE
            vinculo = vinculo_cp(cursor, usuario_id, relatorio["paciente_id"])

            if not vinculo:
                return jsonify({
                    "erro": "Cuidador não está vinculado a este paciente."
                }), 403


        #CAMPOS QUE PODER SER EDITADOS
        campos_permitidos = [
            "alimentacao",
            "higiene",
            "pressao_arterial",
            "glicemia",
            "temperatura",
            "observacoes"
        ]

        for campo in dados:
            if campo not in campos_permitidos:
                return jsonify({
                    "erro": f"O campo '{campo}' não pode ser editado."
                }), 400
            
        campos = []
        valores = []

        for campo in campos_permitidos:
            if campo in dados:
                campos.append(f"{campo} = ?")
                valores.append(dados[campo])

        if not campos:
            return jsonify({
                "erro": "Nenhum campo válido foi enviado para edição."
            }), 400

        valores.append(id)

        #ATUALIZA O RELATORIO
        cursor.execute(f"""
            UPDATE relatorios_diarios
            SET {", ".join(campos)}
            WHERE id = ?
        """, valores)

        conexao.commit()

        return jsonify({
            "msg": "Relatório atualizado com sucesso."
        }), 200

    except Exception as e:
        if conexao:
            conexao.rollback()

        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if conexao:
            conexao.close()

#DESATIVAR RELATORIOS DIARIO
@relatorios_diarios_bp.route("/relatorios_diarios/desativar/<int:id>", methods=['DELETE'])
@jwt_required()
@roles_required("admin")
def desativar_relatorios(id):
    conexao = None

    try:
        conexao = connect()
        cursor = conexao.cursor()

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
                data_horario
            FROM relatorios_diarios
            WHERE id = ?
        """,(id,))

        relatorio = cursor.fetchone()

        if not relatorio:
            return jsonify({
                "erro": "Relatório não encontrado."
            }), 404

        #EXCLUI O RELATORIO
        cursor.execute("""
            DELETE FROM relatorios_diarios
            WHERE id = ?
        """, (id,))

        conexao.commit()

        return jsonify({
            "msg": "Relatório excluído com sucesso.",

            "relatorio_excluido": {
                "id": relatorio["id"],
                "paciente_id": relatorio["paciente_id"],
                "responsavel_id": relatorio["responsavel_id"],
                "alimentacao": relatorio["alimentacao"],
                "higiene": relatorio["higiene"],
                "pressao_arterial": relatorio["pressao_arterial"],
                "glicemia": relatorio["glicemia"],
                "temperatura": relatorio["temperatura"],
                "observacoes": relatorio["observacoes"],
                "data_horario": relatorio["data_horario"]
            }
        }), 200

    except Exception as e:
        if conexao:
            conexao.rollback()

        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if conexao:
            conexao.close()

