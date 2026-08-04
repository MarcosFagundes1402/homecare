from flask import jsonify, request, Blueprint
from database.connect import connect
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.permissoes import admin_required
from werkzeug.security import generate_password_hash
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
        if conexao:
            conexao.close()

# PEGANDO TODOS PACIENTES
@pacientes_bp.route("/pacientes", methods=['GET'])
@jwt_required()
@admin_required()
def mostrar_pacientes():

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
        if conexao: 
            conexao.close()