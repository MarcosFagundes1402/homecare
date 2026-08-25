from flask import Blueprint, jsonify, request
from database.connect import connect
from flask_jwt_extended import jwt_required
from utils.permissoes import admin_required, roles_required

medicamentos_bp = Blueprint("medicamentos",__name__)

#CRIA MEDICAMENTO PARA UM PACIENTE
@medicamentos_bp.route("/medicamentos/criar", methods=['POST'])
@jwt_required()
@admin_required()
def criar_medicamentos():
    conexao = None

    try:
        dados = request.get_json()

        if not dados:
            return jsonify({
                "erro": "Dados não encontrados."
            }), 400

        if "paciente_id" not in dados or "nome" not in dados:
            return jsonify({
                "erro": "O ID do paciente e o nome são obrigatórios."
            }), 400

        conexao = connect()
        cursor = conexao.cursor()

        #VERIFICA SE O PACIENTE EXISTE
        cursor.execute("""
            SELECT
                pacientes.id,
                pacientes.nome,
                usuarios.role
            FROM pacientes
            JOIN usuarios
                ON pacientes.id = usuarios.id
            WHERE pacientes.id = ?
        """,(
            dados["paciente_id"],
        ))

        paciente = cursor.fetchone()

        if not paciente:
            return jsonify({
                "erro": "Paciente não encontrado."
            }), 404
        
        #VERIFICA SE É PACIENTE
        if paciente["role"].lower() != "paciente":
            return jsonify({
                "erro": "O ID informado não pertence a um paciente.",
                "id": paciente["id"],
                "nome": paciente["nome"],
                "role": paciente["role"]
            }), 400
        
        #CRIA O MEDICAMENTO
        cursor.execute("""
            INSERT INTO medicamentos(
                paciente_id,
                nome,
                dosagem,
                horario,
                obs,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """,(
            dados["paciente_id"],
            dados["nome"],
            dados.get("dosagem"),
            dados.get("horario"),
            dados.get("obs"),
            dados.get("status", "ativo")
        ))

        conexao.commit()

        return jsonify({
            "msg": "Medicamento criado com sucesso.",
            "paciente": {
                "id": paciente["id"],
                "nome": paciente["nome"]
            },
            "medicamento": dados["nome"]
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

#CONSULTAR MEDICAMENTOS DE UM PACIENTE
@medicamentos_bp.route("/medicamentos/paciente/<int:id>", methods=['GET'])
@jwt_required()
@roles_required("admin", "cuidador")
def listar_medicamentos_paciente(id):
    conexao = None

    try:
        conexao = connect()
        cursor = conexao.cursor()

        #VERIFICA SE O PACIENTE EXISTE 
        cursor.execute("""
            SELECT 
                pacientes.id,
                pacientes.nome,
                usuarios.role
            FROM pacientes
            JOIN usuarios
                ON pacientes.id = usuarios.id
            WHERE pacientes.id = ?
        """, (id,))

        paciente = cursor.fetchone()

        if not paciente:
            return jsonify({
                "erro": "Paciente não encontrado."
            }), 404

        #VERIFICA SE REALMENTE É PACIENTE
        if paciente["role"].lower() != "paciente":
            return jsonify({
                "erro": "O ID informado não pertence a um paciente."
            }), 400

        #BUSCA O MEDICAMENTO DO PACIENTE
        cursor.execute("""
            SELECT 
                id,
                nome,
                dosagem,
                horario,
                obs,
                status
            FROM medicamentos
            WHERE paciente_id = ?
        """, (id,))

        medicamentos = cursor.fetchall()

        if not medicamentos:
            return jsonify({
                "msg": "Este paciente não possui medicamentos cadastrados."
            }), 200

        lista_medicamento = [dict(medicamento) for medicamento in medicamentos]

        return jsonify({
            "paciente":{
                "id": paciente["id"],
                "nome": paciente["nome"]
            },
            "medicamentos": lista_medicamento
        }), 200

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if conexao:
            conexao.close()

#EDITA UM MEDICAMENTO
@medicamentos_bp.route("/medicamentos/<int:id>", methods=['PATCH'])
@jwt_required()
@admin_required()
def editar_medicamento(id):
    conexao = None

    try:
        dados = request.get_json()

        if not dados:
            return jsonify({
                "erro": "Dados não encontrados."
            }), 400

        conexao = connect()
        cursor = conexao.cursor()

        #VERIFICA SE O MEDICAMENTO EXISTE
        cursor.execute("""
            SELECT id, paciente_id, nome
            FROM medicamentos
            WHERE id =?
        """,(id,))

        medicamento = cursor.fetchone()

        if not medicamento:
            return jsonify({
                "erro": "Medicamento não encontrado."
            }), 404

        #CAMPOS QUE PODE SER EDITADOS
        campos_permitidos = [
            "nome",
            "dosagem",
            "horario",
            "obs",
            "status"
        ]

        campos = []
        valores = []

        for campo in campos_permitidos:
            if campo in dados:
                campos.append(f"{campo} = ?")
                valores.append(dados[campo])

        #VERIFICA SE ALGUM CAMPO VÁLIDO FOI ENVIADO
        if not campos:
            return jsonify({
                "erro": "Nenhum campo válido foi enviado para edição."
            }), 400

        valores.append(id)

        #VAI ATUALIZAR A TABELA
        cursor.execute(f"""
            UPDATE medicamentos
            SET {", ".join(campos)}
            WHERE id =?
        """, valores)

        conexao.commit()

        return jsonify({
            "msg": "Medicamento atualizado com sucesso."
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

#EXCLUIR UM MEDICAMENTO
@medicamentos_bp.route("/medicamentos/<int:id>", methods=['DELETE'])
@jwt_required()
@admin_required()
def excluir_medicamento(id):
    conexao = None

    try:
        conexao = connect()
        cursor = conexao.cursor()

        #VERIFICAR SE O MEDICAMENTO EXISTE
        cursor.execute("""
            SELECT id, nome, paciente_id
            FROM medicamentos
            WHERE id=?
        """, (id,))

        medicamento = cursor.fetchone()

        if not medicamento:
            return jsonify({
                "erro": "Medicamento não encontrado."
            }), 404

        #EXCLUI O MEDICAMENTO
        cursor.execute("""
            DELETE FROM medicamentos
            WHERE id = ?
        """, (id,))

        conexao.commit()

        return jsonify({
            "msg": "Medicamento excluído com sucesso.",
            "medicamento": {
                "id": medicamento["id"],
                "nome": medicamento["nome"]
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
    