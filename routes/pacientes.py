from flask import jsonify, request, Blueprint
from database.connect import connect
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.permissoes import admin_required
from werkzeug.security import generate_password_hash
import sqlite3

pacientes_bp = Blueprint("pacientes", __name__)

# CRIANDO PACIENTE 
@pacientes_bp.route("/pacientes", methods=['POST'])
@jwt_required()
@admin_required()
def criar_pacientes():
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
    conexao.close()

    return jsonify({
        'msg': 'Paciente cadastrado com sucesso'
    }), 201