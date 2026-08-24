from flask import jsonify, request, Blueprint
from database.connect import connect
from flask_jwt_extended import jwt_required
from utils.permissoes import admin_required
import sqlite3

cuidadores_bp = Blueprint("cuidadores", __name__)

# CRIANDO CUIDADO
@cuidadores_bp.route("/cuidadores/criar", methods=['POST'])

def criar_cuidador():

    conexao = None

    try:
        dados = request.get_json()

        if not dados:
            return jsonify({
                'erro': 'Dados não encontrado'
            }), 400

        conexao = connect()
        cursor = conexao.cursor()

        cursor.execute("""
            INSERT INTO cuidadores
            (
                cuidador_id,
                cpf,
                data_nascimento,
                tel,
                endereco,
                obs,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,(
            dados["cuidador_id"],
            dados["cpf"],
            dados["data_nascimento"],
            dados["tel"],
            dados["endereco"],
            dados["obs"],
            dados["status"]
        ))

        conexao.commit()

        return jsonify({
            'msg': 'Cuidador cadastrado com sucesso'
        }), 201

    except sqlite3.IntegrityError:
        return~jsonify({
            'erro': 'CPF já cadastrado'
        }), 400
    
    finally:
        conexao.close()

#CONSULTAR TODOS OS CUIDADORES
@cuidadores_bp.route("/cuidadores", methods=['GET'])
@jwt_required()
@admin_required()
def mostrar_cuidadores():

    try:
        conexao = connect()
        cursor = conexao.cursor()

        cursor.execute("SELECT * FROM cuidadores")

        cuidadores = cursor.fetchall()
        lista_cuidadores = []

        for cuidador in cuidadores:
            dados = dict(cuidador)
            lista_cuidadores.append(dados)

        conexao.close()

        return jsonify(lista_cuidadores), 200
    
    finally:
        conexao.close()

#CONSULTANDO CUIDADORES POR ID
@cuidadores_bp.route("/cuidadores/<int:id>", methods=['GET'])
@jwt_required()
@admin_required()
def consultar_cuidador_id(id):

    conexao = connect()
    cursor= conexao.cursor()

    cursor.execute("""SELECT * FROM cuidadores WHERE id=?""", (id,))

    cuidador = cursor.fetchone()
    conexao.close()

    if cuidador:
        dados = dict(cuidador)
        return jsonify(dados), 200

    return jsonify({
        'erro': 'Cuidador não encontrado'
    }), 404

#EDITAR CUIDADOR TOTAL
@cuidadores_bp.route("/cuidadores/<int:id>", methods=['PUT'])
@jwt_required()
@admin_required()
def editar_cuidador(id):

    cuidador_editado = request.get_json()

    if not cuidador_editado:
        return jsonify({
            'erro': 'Dados não inseridos'
        }), 400

    conexao = connect()
    cursor = conexao.cursor()

    try:
        #verifica se o CPF já existe
        cursor.execute("""
            SELECT id FROM cuidadores WHERE cpf=? AND id !=?
        """, (cuidador_editado['cpf'], id))

        cpf_existente = cursor.fetchone()

        if cpf_existente:
            return jsonify({
                'erro': 'CPF já cadastrado.'
            }), 400

        #atualiza somente o cuidador informado
        cursor.execute("""
            UPDATE cuidadores SET cpf=?, 
            data_nascimento =?,
            tel =?,
            endereco =?,
            obs =?,
            status =?
            WHERE id=?
        """, (
            cuidador_editado["cpf"],
            cuidador_editado["data_nascimento"],
            cuidador_editado["tel"],
            cuidador_editado["endereco"],
            cuidador_editado["obs"],
            cuidador_editado["status"],
            id
        ))

        conexao.commit()

        if cursor.rowcount == 0:
             return jsonify({
                 'erro': 'Cuidador não encontrado.'
             }), 404

        return jsonify({
            'msg': 'Cuidador atualizado com sucesso.'
        }), 200

    except sqlite3.IntegrityError:
        return jsonify({
            'erro': 'CPF já cadastrado.'
        })
    
    finally:
        conexao.close()

#EXCLUIR CUIDADOR
@cuidadores_bp.route("/cuidadores/<int:id>", methods=['DELETE'])
@jwt_required()
@admin_required()
def excluir_cuidador(id):

    conexao = connect()
    cursor = conexao.cursor()

    try:
        cursor.execute("""
            DELETE FROM cuidadores WHERE id=?
        """, (id,))

        conexao.commit()

        if cursor.rowcount == 0:
            return jsonify({
                'erro': 'Cuidador não encontrado'
            }), 404

        return jsonify({
            'msg': 'Cuidador excluido com sucesso.'
        }), 200
    finally:
        conexao.close()