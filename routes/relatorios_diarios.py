from flask import Blueprint, jsonify, request
from database.connect import connect
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.permissoes import admin_required, roles_required
from datetime import datetime

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

        usuario_id = get_jwt_identity()

        conexao = connect()
        cursor = conexao.cursor()

        #BUSCAR O USUARIO LOGADO
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
        """, (dados["paciente_id"],))

        paciente = cursor.fetchone()

        if not paciente:
            return jsonify({
                "erro": "Paciente não encontrado."
            }), 404

        #SE FOR CUIDADOR, VERIFICA SE ESTÁ VINCULADO AO PACIENTE
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
#@jwt_required()
#@roles_required("admin", "cuidador")
def listar_relatorios_paciente(paciente_id):
    conexao= None

    try:
        #usuario = get_jwt_identity()
        usuario_id = 5

        conexao = connect()
        cursor = conexao.cursor()

        #BUSCAR USUARIO LOGADO
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

        #VERIFICA VINCULO ENTRE CUIDADOR E PACIENTE
        if usuario["role"].lower() == "cuidador":

            cursor.execute("""
                SELECT id
                FROM cuidadores_pacientes
                WHERE cuidador_id = ?
                AND paciente_id = ?
            """,(
                usuario_id,
                paciente_id
            ))

            vinculo = cursor.fetchone()

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