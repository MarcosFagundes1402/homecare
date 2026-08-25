from flask import Blueprint, jsonify, request

from database.connect import connect

from flask_jwt_extended import jwt_required

from utils.permissoes import admin_required


cuidadores_pacientes_bp = Blueprint(
    "cuidadores_pacientes",
    __name__
)


# CRIA O VINCULO ENTRE CUIDADOR E PACIENTE
@cuidadores_pacientes_bp.route("/cuidadores_pacientes/vinculo", methods=["POST"])
@jwt_required()
@admin_required()
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
        cursor.execute("""
            SELECT id, nome, role
            FROM usuarios
            WHERE id = ?
        """, (
            dados["cuidador_id"],
        ))

        cuidador = cursor.fetchone()

        if not cuidador:
            return jsonify({
                "erro": "ID do cuidador não encontrado."
            }), 404

        # VERIFICA SE REALMENTE É CUIDADOR
        if cuidador["role"].lower() != "cuidador":
            return jsonify({
                "erro": "O ID informado como cuidador não pertence a um cuidador.",
                "id": cuidador["id"],
                "nome": cuidador["nome"],
                "role": cuidador["role"]
            }), 400

        # VERIFICA SE O ID INFORMADO COMO PACIENTE EXISTE
        cursor.execute("""
            SELECT id, nome, role
            FROM usuarios
            WHERE id = ?
        """, (
            dados["paciente_id"],
        ))

        paciente = cursor.fetchone()

        if not paciente:
            return jsonify({
                "erro": "ID do paciente não encontrado."
            }), 404

        # VERIFICA SE REALMENTE É PACIENTE
        if paciente["role"].lower() != "paciente":
            return jsonify({
                "erro": "O ID informado como paciente não pertence a um paciente.",
                "id": paciente["id"],
                "nome": paciente["nome"],
                "role": paciente["role"]
            }), 400

        # VERIFICA SE O VINCULO JÁ EXISTE
        cursor.execute("""
            SELECT id
            FROM cuidadores_pacientes
            WHERE cuidador_id = ?
            AND paciente_id = ?
        """, (
            dados["cuidador_id"],
            dados["paciente_id"]
        ))

        vinculo = cursor.fetchone()

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
@admin_required()
def listar_pacientes_cuidador(id):

    conexao = None

    try:
        conexao = connect()
        cursor = conexao.cursor()

        # VERIFICA SE O USUARIO EXISTE
        cursor.execute("""
                SELECT id, nome, role
                FROM usuarios
                WHERE id = ?
            """, (id,))

        usuario = cursor.fetchone()

        if not usuario:
            conexao.close()

            return jsonify({
                "erro": "Usuário não encontrado."
            }), 404

        # VERIFICA SE REALMENTE É CUIDADOR
        if usuario["role"].lower() != "cuidador":
            conexao.close()

            return jsonify({
                "erro": "O usuário não é cuidador.",
                "usuario": usuario["nome"],
                "role": usuario["role"]
            }), 400

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
            conexao.close()

            return jsonify({
                "msg": "Este cuidador não possui pacientes vinculados."
            }), 200

        lista = [dict(paciente) for paciente in pacientes]

        conexao.close()

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
@admin_required()
def listar_cuidadores_paciente(id):

    conexao = None

    try:
        conexao = connect()
        cursor = conexao.cursor()

        # VERIFICA SE O USUARIO EXISTE
        cursor.execute("""
            SELECT id, nome, role
            FROM usuarios
            WHERE id = ?
        """, (id,))

        usuario = cursor.fetchone()

        if not usuario:
            conexao.close()

            return jsonify({
                "erro": "Usuário não encontrado."
            }), 404

        # VERIFICA SE REALMENTE É PACIENTE
        if usuario["role"].lower() != "paciente":
            conexao.close()

            return jsonify({
                "erro": "O usuário não é paciente.",
                "usuario": usuario["nome"],
                "role": usuario["role"]
            }), 400

        # BUSCA OS CUIDADORES VINCULADOS
        cursor.execute("""
            SELECT
                c.id,
                c.nome,
                c.cpf,
                c.data_nascimento,
                c.tel,
                c.endereco,
                c.obs,
                c.status

            FROM cuidadores_pacientes cp

            JOIN cuidadores c
                ON cp.cuidador_id = c.id

            WHERE cp.paciente_id = ?
        """, (id,))

        cuidadores = cursor.fetchall()

        if not cuidadores:
            conexao.close()

            return jsonify({
                "msg": "Este paciente não possui cuidadores vinculados."
            }), 200

        lista = [dict(cuidador) for cuidador in cuidadores]

        conexao.close()

        return jsonify(lista), 200

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if conexao:
            conexao.close()

# REMOVE O VINCULO ENTRE CUIDADOR E PACIENTE


@cuidadores_pacientes_bp.route("/cuidadores_pacientes/vinculo", methods=["DELETE"])
@jwt_required()
@admin_required()
def remover_vinculo():

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

        # VERIFICA SE O VINCULO EXISTE
        cursor.execute("""
            SELECT id
            FROM cuidadores_pacientes
            WHERE cuidador_id = ?
            AND paciente_id = ?
        """, (
            dados["cuidador_id"],
            dados["paciente_id"]
        ))

        vinculo = cursor.fetchone()

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
            "cuidador_id": dados["cuidador_id"],
            "paciente_id": dados["paciente_id"]
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
