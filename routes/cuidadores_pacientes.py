from flask import Blueprint, jsonify, request
from database.connect import connect
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils import (
        roles_required,
        cuidador_status,
        paciente_status,
        vinculo_cp,
        buscar_role,
        erro_role,
    ) 


cuidadores_pacientes_bp = Blueprint("cuidadores_pacientes", __name__)

# CRIA O VINCULO ENTRE CUIDADOR E PACIENTE
@cuidadores_pacientes_bp.route("/cuidadores_pacientes/criar-vinculo", methods=["POST"])
@jwt_required()
@roles_required("admin")
def criar_vinculo():

    conexao = None

    try:
        dados = request.get_json()

        if not dados:
            return jsonify({
                "erro": "Dados não encontrados."
            }), 400

        if "cuidador_id" not in dados or "paciente_id" not in dados:
            return jsonify({
                "erro": "cuidador_id e paciente_id são obrigatórios."
            }), 400

        conexao = connect()
        cursor = conexao.cursor()

        # VERIFICA SE O ID INFORMADO COMO CUIDADOR EXISTE
        cuidador, erro, role_nome = buscar_role(cursor, dados["cuidador_id"], "cuidador")

        # RETORNA ERRO SE O USUARIO NAO EXISTIR OU A ROLE FOR INVALIDA
        if erro:
            return erro_role(erro, role_nome, cuidador)
        
        #VERIFICA SE EXISTE NA TABELA CUIDADORES
        cuidador_cadastrado = cuidador_status(cursor, dados["cuidador_id"])

        if not cuidador_cadastrado:
            return jsonify({
                "erro": "Cadastro de cuidador não encontrado."
            }), 404

        if cuidador_cadastrado["status"] == "inativo":
            return jsonify({
                "erro": "Não é possível vincular um cuidador inativo."
            }), 400
        
        # VERIFICA SE O ID INFORMADO COMO PACIENTE EXISTE
        paciente, erro, role_nome = buscar_role(cursor, dados["paciente_id"], "paciente")

        # RETORNA ERRO SE O USUARIO NAO EXISTIR OU A ROLE FOR INVALIDA
        if erro:
            return erro_role(erro, role_nome, paciente)
        

        #VERIFICA SE EXISTE NA TABELA PACIENTES
        paciente_cadastrado = paciente_status(cursor, dados["paciente_id"])

        if not paciente_cadastrado:
            return jsonify({
                "erro": "Cadastro de paciente não encontrado."
            }), 404

        if paciente_cadastrado["status"] == "inativo":
            return jsonify({
                "erro":"Não é possível vincular um paciente inativo."
            }), 400
        
        # VERIFICA SE O VINCULO JÁ EXISTE
        vinculo = vinculo_cp(cursor, dados["cuidador_id"], dados["paciente_id"])
 
        if vinculo:
            return jsonify({
                "erro": "Este cuidador já está vinculado a este paciente."
            }), 409

        # CRIA O VINCULO
        cursor.execute("""
            INSERT INTO cuidadores_pacientes (
                cuidador_id,
                paciente_id
            )
            VALUES (?, ?)
        """, (
            dados["cuidador_id"],
            dados["paciente_id"]
        ))

        conexao.commit()

        return jsonify({
            "msg": "Vínculo criado com sucesso.",
            "cuidador": {
                "id": cuidador["id"],
                "nome": cuidador["nome"]
            },
            "paciente": {
                "id": paciente["id"],
                "nome": paciente["nome"]
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


# MOSTRA OS PACIENTES QUE O CUIDADOR TEM
@cuidadores_pacientes_bp.route("/cuidadores_pacientes/cuidador/<int:id>", methods=["GET"])
@jwt_required()
@roles_required("admin")
def listar_pacientes_cuidador(id):

    conexao = None

    try:
        conexao = connect()
        cursor = conexao.cursor()

        # VERIFICA SE O ID INFORMADO COMO CUIDADOR EXISTE
        cuidador, erro, role_nome = buscar_role(cursor, id, "cuidador")

        print("erro:", repr(erro))
        print("role_nome:", role_nome)

        # RETORNA O ERRO SE A ROLE NAO EXISTIR
        if erro:
            return erro_role(erro, role_nome, cuidador)

   
        # BUSCA OS PACIENTES VINCULADOS
        cursor.execute("""
                SELECT
                    pacientes.id,
                    pacientes.nome,
                    pacientes.cpf,
                    pacientes.data_nascimento,
                    pacientes.tel,
                    pacientes.endereco,
                    pacientes.obs
                FROM cuidadores_pacientes
                JOIN pacientes
                    ON cuidadores_pacientes.paciente_id = pacientes.id
                WHERE cuidadores_pacientes.cuidador_id = ?
            """, (id,))

        pacientes = cursor.fetchall()

        if not pacientes:
            return jsonify({
                "msg": "Este cuidador não possui pacientes vinculados."
            }), 200

        lista = [dict(paciente) for paciente in pacientes]

        return jsonify(lista), 200

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if conexao:
            conexao.close()

# MOSTRA QUAIS CUIDADORES CUIDAM DO PACIENTE
@cuidadores_pacientes_bp.route("/cuidadores_pacientes/paciente/<int:id>", methods=["GET"])
@jwt_required()
@roles_required("admin")
def listar_cuidadores_paciente(id):
    conexao = None

    try:
        conexao = connect()
        cursor = conexao.cursor()

        # VERIFICA SE O ID INFORMADO COMO PACIENTE EXISTE
        paciente, erro, role_nome = buscar_role(cursor, id, "paciente")

        # RETORNA O ERRO SE A ROLE NAO EXISTIR
        if erro:
            return erro_role(erro, role_nome, paciente)

        # BUSCA OS CUIDADORES VINCULADOS
        cursor.execute("""
            SELECT
                cuidadores.id,
                cuidadores.nome,
                cuidadores.cpf,
                cuidadores.data_nascimento,
                cuidadores.tel,
                cuidadores.endereco,
                cuidadores.obs,
                cuidadores.status

            FROM cuidadores_pacientes

            JOIN cuidadores
                ON cuidadores_pacientes.cuidador_id = cuidadores.id

            WHERE cuidadores_pacientes.paciente_id = ?
        """, (id,))

        cuidadores = cursor.fetchall()

        if not cuidadores:
            return jsonify({
                "msg": "Este paciente não possui cuidadores vinculados."
            }), 200

        lista = [dict(cuidador) for cuidador in cuidadores]

        return jsonify(lista), 200

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if conexao:
            conexao.close()

#CUIDADOR CONSULTA OS PRÓPRIOS PACIENTES
@cuidadores_pacientes_bp.route("/cuidadores_pacientes/meus-pacientes", methods=['GET'])
@jwt_required()
@roles_required("cuidador")
def meus_pacientes():
    conexao = None

    try:
        conexao = connect()
        cursor = conexao.cursor()

        cuidador_id = get_jwt_identity()

        cursor.execute("""
            SELECT 
                pacientes.id,
                pacientes.nome,
                pacientes.cpf,
                pacientes.data_nascimento,
                pacientes.tel,
                pacientes.endereco,
                pacientes.obs,
                pacientes.status
            FROM cuidadores_pacientes
            JOIN pacientes
                ON cuidadores_pacientes.paciente_id = pacientes.id
            WHERE cuidadores_pacientes.cuidador_id = ?
        """, (cuidador_id,))

        pacientes = cursor.fetchall()

        if not pacientes:
            return jsonify({
                "erro": "Você não possui pacientes vinculados."
            }), 200

        lista = [dict(paciente) for paciente in pacientes]

        return jsonify(lista), 200
    
    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if conexao:
            conexao.close()

#PACIENTE CONSULTA OS PROPRIOS CUIDADORES
@cuidadores_pacientes_bp.route("/cuidadores_pacientes/meus-cuidadores", methods=['GET'])
@jwt_required()
@roles_required("paciente")
def meus_cuidadores():
    conexao = None

    try:
        conexao = connect()
        cursor = conexao.cursor()

        paciente_id = get_jwt_identity()

        cursor.execute("""
            SELECT 
                cuidadores.id,
                cuidadores.nome,
                cuidadores.cpf,
                cuidadores.data_nascimento,
                cuidadores.tel,
                cuidadores.endereco,
                cuidadores.obs,
                cuidadores.status

            FROM cuidadores_pacientes
            
            JOIN cuidadores
                ON cuidadores_pacientes.cuidador_id = cuidadores.id
            WHERE cuidadores_pacientes.paciente_id = ?
        """, (paciente_id,))

        cuidadores = cursor.fetchall()

        if not cuidadores:
            return jsonify({
                "erro": "Você não possui cuidadores vinculados."
            }), 200

        lista = [dict(cuidador) for cuidador in cuidadores]

        return jsonify(lista), 200

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if conexao:
            conexao.close()

# REMOVE O VINCULO ENTRE CUIDADOR E PACIENTE
@cuidadores_pacientes_bp.route("/cuidadores_pacientes/deletar-vinculo", methods=["DELETE"])
@jwt_required()
@roles_required("admin")
def remover_vinculo():

    conexao = None

    try:
        dados = request.get_json()

        #VERIFICA SE FORAM ENVIADOS DADOS
        if not dados:
            return jsonify({
                "erro": "Dados não encontrados."
            }), 400

        #VERIFICA SE OS IDS FORAM INFORMADOS
        if not dados.get("cuidador_id") or not dados.get("paciente_id"):
            return jsonify({
                "erro": "cuidador_id e paciente_id são obrigatórios."
            }), 400
        
        conexao = connect()
        cursor = conexao.cursor()

        # BUSCA CUIDADOR E PACIENTE
        cursor.execute("""
            SELECT id, nome, role
            FROM usuarios
            WHERE id IN (?, ?)
        """,(
            dados["cuidador_id"],
            dados["paciente_id"]
        ))

        usuarios = cursor.fetchall()

        cuidador = None
        paciente = None

        #IDENTIFICA QUAL REGISTRO É CUIDADOR/PACIENTE
        for usuario in usuarios:
            if usuario["id"] == dados["cuidador_id"]:
                cuidador = usuario

            if usuario["id"] == dados["paciente_id"]:
                paciente = usuario

        #VERIFICA SE O CUIDADOR EXISTE
        if not cuidador:
            return jsonify({
                "erro": "Cuidador não encontrado."
            }), 404

        #VERIFICA SE REALMENTE É CUIDADOR
        if cuidador["role"].lower() != "cuidador":
            return jsonify({
                "erro": "O cuidador_id informado não pertence a um cuidador."
            }), 400
        
        #VERIFICA SE O PACIENTE EXISTE
        if not paciente:
            return jsonify({
                "erro": "Paciente não encontrado."
            }), 404
        
        # VERIFICA SE O ID É REALMENTE DE PACIENTE
        if paciente["role"].lower() != "paciente":
            return jsonify({
                "erro": "O paciente_id não pertence a um paciente."
            }), 400

        # VERIFICA SE O VINCULO EXISTE
        vinculo = vinculo_cp(cursor, dados["cuidador_id"], dados["paciente_id"])

        if not vinculo:
            return jsonify({
                "erro": "Vínculo não encontrado."
            }), 404

        # REMOVE O VINCULO
        cursor.execute("""
            DELETE FROM cuidadores_pacientes
            WHERE cuidador_id = ?
            AND paciente_id = ?
        """, (
            dados["cuidador_id"],
            dados["paciente_id"]
        ))

        conexao.commit()

        return jsonify({
            "msg": "Vínculo removido com sucesso.",

            "vinculo_removido": {
                "cuidador": {
                    "id": cuidador["id"],
                    "nome": cuidador["nome"]
                },
                "paciente": {
                    "id": paciente["id"],
                    "nome": paciente["nome"]
                }
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
