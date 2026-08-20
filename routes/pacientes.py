from flask import jsonify, request, Blueprint
from database.connect import connect
from flask_jwt_extended import jwt_required
from utils.permissoes import admin_required
import sqlite3

pacientes_bp = Blueprint("pacientes", __name__)

# CRIANDO PACIENTE 
@pacientes_bp.route("/pacientes/criar", methods=['POST'])
@jwt_required()
@admin_required()
def criar_pacientes():

    conexao = None

    try:
        dados = request.get_json()

        if not dados:
            return jsonify({
                'erro': 'Dados não enviados'
            }), 400
        
        conexao = connect()
        cursor = conexao.cursor()

        cursor.execute("""
        INSERT INTO pacientes
        (
            usuario_id,
            cpf,
            data_nascimento,
            tel,
            endereco,
            obs
        )

        VALUES (?, ?, ?, ?, ?, ?)
        """,(
            dados["usuario_id"],
            dados["cpf"],
            dados["data_nascimento"],
            dados["tel"],
            dados["endereco"],
            dados["obs"]
        ))

        conexao.commit()

        return jsonify({
            'msg': 'Paciente cadastrado com sucesso'
        }), 201
    
    except sqlite3.IntegrityError:
        return jsonify({
            "erro": "CPF já cadastrado."
        }), 400

    finally:
        conexao.close()

# CONSULTADO TODOS PACIENTES
@pacientes_bp.route("/pacientes", methods=['GET'])
@jwt_required()
@admin_required()
def mostrar_pacientes():

    conexao = None

    try: 
        conexao = connect()
        cursor = conexao.cursor()

        cursor.execute("SELECT * FROM pacientes")

        pacientes = cursor.fetchall()

        lista_pacientes = []

        for paciente in pacientes:
            dados = dict(paciente)
            lista_pacientes.append(dados)

        conexao.close()

        return jsonify (lista_pacientes), 200

    finally:
        conexao.close()

#CONSULTANDO PACIENTES POR ID
@pacientes_bp.route('/pacientes/<int:id>', methods=['GET'])
@jwt_required()
@admin_required()
def consultar_paciente_id(id):

    conexao = connect()
    cursor = conexao.cursor()

    cursor.execute("""SELECT * FROM pacientes WHERE id=?""", (id,))

    paciente = cursor.fetchone()
    conexao.close()

    if paciente:
        dados = dict(paciente)   

        return jsonify(dados),200

    return jsonify({
        "erro": "Paciente não encontrado"
    }), 404

#EDITAR PACIENTE TOTAL
@pacientes_bp.route('/pacientes/<int:id>', methods=['PUT'])
@jwt_required()
@admin_required()
def editar_paciente(id):

    paciente_editado = request.get_json()

    if not paciente_editado:
        return jsonify({
            "erro": "Dados não inseridos"
        }), 400

    conexao = connect()
    cursor = conexao.cursor()

    try: 
        #Verifica se o CPF já existe
        cursor.execute("""
            SELECT id FROM pacientes WHERE cpf =? AND id !=?
        """, (paciente_editado["cpf"], id))

        cpf_existente = cursor.fetchone()

        if cpf_existente:
            return jsonify({
                "erro": "CPF já cadastrado."
            }), 400

        #atualiza somente o paciente informado
        cursor.execute("""
        UPDATE pacientes 
        SET 
        cpf=?,
        data_nascimento =?,
        tel=?, endereco=?,
        obs=?
        WHERE id=?
        """, (
            paciente_editado["cpf"],
            paciente_editado["data_nascimento"],
            paciente_editado["tel"],
            paciente_editado["endereco"],
            paciente_editado["obs"],
            id
        ))

        conexao.commit()

        if cursor.rowcount == 0:
            return jsonify({
                "erro": "Paciente não encontrado"
            }), 404
        return jsonify({
            "msg": "Paciente atualizado com sucesso"
        }),200
    
    except sqlite3.IntegrityError:
        return jsonify({
            "erro": "CPF  já cadastrado"
        })
    finally:
        conexao.close()

# EXCLUIR PACIENTE 
@pacientes_bp.route('/pacientes/<int:id>', methods=['DELETE'])
@jwt_required()
@admin_required()
def excluir_paciente(id):

    conexao = connect()
    cursor = conexao.cursor()

    try:
        cursor.execute("""
            DELETE FROM pacientes WHERE id=?
        """, (id,))

        conexao.commit()

        if cursor.rowcount == 0:
            return jsonify({
                "erro": "Paciente não encontrado"
            }), 404
        return jsonify({
            "msg": "Paciente excluido com sucesso"
        }), 200
    finally:
        conexao.close()