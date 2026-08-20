from flask import Blueprint, jsonify, request
from database.connect import connect
from flask_jwt_extended import jwt_required
from utils.permissoes import admin_required

cuidadores_pacientes_bp = Blueprint("cuidadores_paciente", __name__)

#CRIA O VINCULO ENTRE CUIDADOR E PACIENTE
@cuidadores_pacientes_bp.route("/cuidadores_paciente/criar", methods=['GET'])
def criar_vinculo():

    conexao = None

    try:
        dados = request.get_json()

        if not dados:
            return jsonify({
                'erro': 'Dados não encontrado'
            })