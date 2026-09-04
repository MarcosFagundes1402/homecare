from flask import jsonify, request, Blueprint
from database.connect import connect
from flask_jwt_extended import jwt_required
import sqlite3
from utils import (
    roles_required,
    buscar_role,
    erro_role,
    cuidador_status
    )

cuidadores_bp = Blueprint("cuidadores", __name__)

# CRIAR CUIDADOR
@cuidadores_bp.route("/cuidadores/criar", methods=['POST'])
@jwt_required()
@roles_required("admin")
def criar_cuidador():

    conexao = None

    try:
        dados = request.get_json()

        if not dados:
            return jsonify({
                'erro': 'Dados não encontrado.'
            }), 400

        campos_obrigatorios = [
            "id",
            "cpf",
            "data_nascimento",
            "tel",
            "endereco"
        ]

        for campo in campos_obrigatorios:
            if campo not in dados or dados[campo] is None or dados[campo] == "":
                return jsonify({
                    "erro": f"O campo '{campo}' é obrigatório."
                }), 400
            
        conexao = connect()
        cursor = conexao.cursor()

        #VERIFICA SE O ID PERTENCE A UM CUIDADOR
        cuidador, erro, role_nome = buscar_role(cursor, dados["id"], "cuidador")

        if erro:
            return erro_role(erro, role_nome, cuidador)

        #VERIFICA SE JA POSSUI CADASTRO
        cuidador_cadastrado = cuidador_status(cursor, dados["id"])

        if cuidador_cadastrado:
            return jsonify({
                "erro": "Este cuidador já possui cadastro."
            }), 409

        #CRIA O CUIDADOR
        cursor.execute("""
            INSERT INTO cuidadores
            (
                id,
                cpf,
                data_nascimento,
                tel,
                endereco,
                obs,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,(
            dados["id"],
            dados["cpf"],
            dados["data_nascimento"],
            dados["tel"],
            dados["endereco"],
            dados.get("obs"),
            "ativo"
        ))

        conexao.commit()

        return jsonify({
            'msg': 'Cuidador cadastrado com sucesso.',
            "cuidador_id": dados["id"]
        }), 201

    except sqlite3.IntegrityError:
        if conexao:
            conexao.rollback()

        return jsonify({
            'erro': 'CPF já cadastrado.'
        }), 400
    except Exception as e:
        if conexao:
            conexao.rollback()

        return jsonify({
            "erro": str(e)
        }), 500
    
    finally:
        if conexao:
            conexao.close()

#CONSULTAR TODOS OS CUIDADORES
@cuidadores_bp.route("/cuidadores", methods=['GET'])
@jwt_required()
@roles_required("admin")
def mostrar_cuidadores():
    conexao = None

    try:
        conexao = connect()
        cursor = conexao.cursor()

        cursor.execute("SELECT * FROM cuidadores")

        cuidadores = cursor.fetchall()
        lista_cuidadores = [dict(cuidador) for cuidador in cuidadores]

        return jsonify(lista_cuidadores), 200
    
    finally:
        if conexao:
            conexao.close()

#CONSULTANDO CUIDADORES POR ID
@cuidadores_bp.route("/cuidadores/<int:id>", methods=['GET'])
@jwt_required()
@roles_required("admin")
def consultar_cuidador_id(id):
    conexao = None

    try:
        conexao = connect()
        cursor = conexao.cursor()

        #VALIDA SE O ID PERTENCE A UM CUIDADOR
        cuidador, erro, role_nome = buscar_role(cursor, id, "cuidador")

        if erro:
            return erro_role(erro, role_nome, cuidador)

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
        """, (id,))

        dados_cuidador = cursor.fetchone()

        if not dados_cuidador:
            return jsonify({
                "erro": "Cuidador não encontrado."
            }), 404

        return jsonify({
            "cuidador": {
                "id": cuidador["id"],
                "nome": cuidador["nome"],
                "cpf": dados_cuidador["cpf"],
                "data_nascimento": dados_cuidador["data_nascimento"],
                "tel": dados_cuidador["tel"],
                "endereco": dados_cuidador["endereco"],
                "obs": dados_cuidador["obs"],
                "status": dados_cuidador["status"]
            }
        }), 200

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if conexao:
            conexao.close()

#EDITAR CUIDADOR 
@cuidadores_bp.route("/cuidadores/editar/<int:id>", methods=['PATCH'])
@jwt_required()
@roles_required("admin")
def editar_cuidador(id):
    conexao = None

    try:
        dados = request.get_json()

        if not dados:
            return jsonify({
                "erro": "Dados não encontrados."
            }), 400

        conexao = connect()
        cursor = conexao.cursor()

        #VALIDA SE O ID PERTENCE A UM CUIDADOR
        cuidador, erro, role_nome = buscar_role(cursor, id, "cuidador")

        if erro:
            return erro_role(erro, role_nome, cuidador)

        #CAMPOS QUE PODEM SER EDITADOS
        campos_permitidos = [
            "cpf",
            "data_nascimento",
            "tel",
            "endereco",
            "obs"
        ]

        #VALIDA O CAMPO NAO PERMITIDOS
        for campo in dados:
            if campo not in campos_permitidos:
                return jsonify({
                    "erro": f"O campo '{campo}' não pode ser editado."
                }), 400

        #VERIFICA CPF DUPLICADO
        if "cpf" in dados:
            if dados["cpf"] is None or dados["cpf"] == "":
                return jsonify({
                    "erro": "O campo 'cpf' não pode estar vazio."
                }), 400

            cursor.execute("""
                SELECT id
                FROM cuidadores
                WHERE cpf = ?
                AND id != ?
            """, (
                dados["cpf"],
                id
            ))

            cpf_existente = cursor.fetchone()

            if cpf_existente:
                return jsonify({
                    "erro": "CPF já cadastrado."
                }), 400

        #MONTA UPDATE DINAMICO
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

        #ATUALIZAR CUIDADOR
        cursor.execute(f"""
            UPDATE cuidadores
            SET {", ".join(campos)}
            WHERE id = ?
        """, valores)

        conexao.commit()

        return jsonify({
            "msg": "Cuidador atualizado com sucesso.",
            "cuidador_id": id,
            "campos_atualizados": dados
        }), 200

    except sqlite3.IntegrityError:
        if conexao:
            conexao.rollback()

        return jsonify({
            "erro": "CPF já cadastrado."
        }), 400

    except Exception as e:
        if conexao:
            conexao.rollback()

        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if conexao:
            conexao.close()

#DESATIVAR CUIDADOR
@cuidadores_bp.route("/cuidadores/desativar/<int:id>", methods=['DELETE'])
@jwt_required()
@roles_required("admin")
def excluir_cuidador(id):
    conexao = None

    try:
        conexao = connect()
        cursor = conexao.cursor()

        #VALIDA SE O ID PERTENCE A UM CUIDADOR
        cuidador, erro, role_nome = buscar_role(cursor, id, "cuidador")

        if erro:
            return erro_role(erro, role_nome, cuidador)

        #VERIFICA STATUS DO CUIDADOR
        cuidador_cadastrado = cuidador_status(cursor, id)

        if not cuidador_cadastrado:
            return jsonify({
                "erro": "Cuidador não encontrado."
            }), 404

        if cuidador_cadastrado["status"] == "inativo":
            return jsonify({
                "erro": "Cuidador já inativo."
            }), 400

        #DESATIVA CUIDADOR
        cursor.execute("""
            UPDATE cuidadores
            SET status = 'inativo'
            WHERE id = ?
        """, (id,))

        conexao.commit()

        return jsonify({
            "msg": "Cuidador desativado com sucesso.",

            "cuidador": {
                "id": cuidador["id"],
                "nome": cuidador["nome"],
                "status": "inativo"
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