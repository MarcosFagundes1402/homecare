from flask import jsonify, request, Blueprint
from database.connect import connect
from flask_jwt_extended import jwt_required
import sqlite3
from utils import (
    roles_required,
    buscar_role,
    erro_role,
    paciente_status
    )

pacientes_bp = Blueprint("pacientes", __name__)

# CRIANDO PACIENTE 
@pacientes_bp.route("/pacientes/criar", methods=['POST'])
@jwt_required()
@roles_required("admin")
def criar_pacientes():

    conexao = None

    try:
        dados = request.get_json()

        if not dados:
            return jsonify({
                'erro': 'Dados não enviados'
            }), 400
        
        #CAMPOS OBRIGATORIOS
        campos_obrigatorios = [
            "id",
            "cpf",
            "data_nascimento",
            "tel",
            "endereco"
        ]

        for campo in campos_obrigatorios:
            if campo not in dados or dados[campo] is None or dados [campo] == "":
                return jsonify({
                    "erro": f"O campo '{campo}' é obrigatório."
                }), 400
            
        conexao = connect()
        cursor = conexao.cursor()

        paciente, erro, role_nome = buscar_role(cursor, dados["id"], "paciente")

        if erro:
            return erro_role(erro, role_nome, paciente)

        # VERIFICA SE JÁ POSSUI CADASTRO DE PACIENTE
        paciente_cadastrado = paciente_status(cursor, dados["id"])

        if paciente_cadastrado:
            return jsonify({
                "erro": "Este paciente já possui cadastro."
            }), 409

        # CRIA O PACIENTE
        
        cursor.execute("""
        INSERT INTO pacientes
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
            dados.get("status", "ativo")
        ))

        conexao.commit()

        return jsonify({
            "msg": "Paciente cadastrado com sucesso",
            "paciente_id": dados["id"]
        }), 201
    
    except sqlite3.IntegrityError:
        if conexao:
            conexao.rollback()

        return jsonify({
            "erro": "CPF já cadastrado."
        }), 400

    finally:
        if conexao:
            conexao.close()

# CONSULTADO TODOS PACIENTES
@pacientes_bp.route("/pacientes/consulta", methods=['GET'])
@jwt_required()
@roles_required("admin")
def mostrar_pacientes():

    conexao = None

    try: 
        conexao = connect()
        cursor = conexao.cursor()

        cursor.execute("SELECT * FROM pacientes")

        pacientes = cursor.fetchall()

        lista_pacientes = [dict(paciente) for paciente in pacientes]

        return jsonify (lista_pacientes), 200

    finally:
        if conexao:
            conexao.close()

#CONSULTANDO PACIENTES POR ID
@pacientes_bp.route('/pacientes/consultar/<int:id>', methods=['GET'])
@jwt_required()
@roles_required("admin")
def consultar_paciente_id(id):
    conexao = None

    try:
        conexao = connect()
        cursor = conexao.cursor()

        #VALIDA SE O ID PERTENCE A UM PACIENTE
        paciente, erro, role_nome = buscar_role(cursor, id, "paciente")

        if erro:
            return erro_role(erro, role_nome, paciente)

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
        """, (id, ))

        dados_paciente = cursor.fetchone()

        if not dados_paciente:
            return jsonify({
                "erro": "Paciente não encontrado."
            }), 404

        return jsonify({
            "paciente": {
                "id": paciente["id"],
                "nome": paciente["nome"],
                "cpf": dados_paciente["cpf"],
                "data_nascimento": dados_paciente["data_nascimento"],
                "tel": dados_paciente["tel"],
                "endereco": dados_paciente["endereco"],
                "obs": dados_paciente["obs"],
                "status": dados_paciente["status"]
            }
        }), 200

    except Exception as e:
        return jsonify ({
            "erro": str(e)
        }), 500

    finally:
        if conexao:
            conexao.close()

#EDITAR PACIENTE
@pacientes_bp.route('/pacientes/editar/<int:id>', methods=['PATCH'])
@jwt_required()
@roles_required("admin")
def editar_paciente(id):

    conexao = None

    try: 
        dados = request.get_json()

        if not dados:
            return jsonify({
                "erro": "Dados não encontrados."
            }), 400

        
        conexao = connect()
        cursor = conexao.cursor()

        #VALIDA SE O ID PERTENCE A UM PACIENTE
        paciente, erro, role_nome = buscar_role(cursor, id, "paciente")

        if erro:
            return erro_role(erro, role_nome, paciente)

        #CAMPOS QUE PODEM SER EDITADOS
        campos_permitidos = [
            "cpf",
            "data_nascimento",
            "tel",
            "endereco",
            "obs"
        ]

        #VALIDA CAMPO NAO PERMITIDO
        for campo in dados:
            if campo not in campos_permitidos:
                return jsonify({
                    "erro": f"O campo '{campo}' não pode ser editado."
                }), 400

        #SE O CPF ENVIADO, VERIFICA DUPLICIDADE
        if "cpf" in dados:

            if dados["cpf"] is None or dados ["cpf"] == "":
                return jsonify({
                    "erro": "O campo 'cpf' não pode estar vazio."
                }), 400

            cursor.execute("""
                SELECT id
                FROM pacientes
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

        #ATUALIZA PACIENTE
        cursor.execute(f"""
            UPDATE pacientes
            SET {", ".join(campos)}
            WHERE id = ?
        """, valores)

        conexao.commit()

        return jsonify({
            "msg": "Paciente atualizado com sucesso.",
            "paciente_id": id,

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

# EXCLUIR PACIENTE 
@pacientes_bp.route('/pacientes/desativar/<int:id>', methods=['DELETE'])
@jwt_required()
@roles_required("admin")
def excluir_paciente(id):

    conexao = None

    try:
        conexao = connect()
        cursor = conexao.cursor()

        paciente, erro, role_nome = buscar_role(cursor, id, "paciente")

        if erro:
            return erro_role(erro, role_nome, paciente)
        
        paciente_cadastrado = paciente_status(cursor, id)

        if not paciente_cadastrado:
            return jsonify({
                "erro": "Paciente não encontrado."
            }), 404

        if paciente_cadastrado["status"] == "inativo":
            return jsonify({
                "erro": "Paciente já inativo."
            }), 400
        
        cursor.execute("""
            UPDATE pacientes
            SET status = 'inativo'
            WHERE id = ?
        """, (id,))

        conexao.commit()

        return jsonify({
            "msg": "Paciente desativado com sucesso.",

            "paciente": {
                "id": paciente["id"],
                "nome": paciente["nome"],
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