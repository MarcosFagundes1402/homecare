from flask import Blueprint, request, jsonify
from database.connect import connect
from flask_jwt_extended import create_access_token

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=['POST'])
def login():
    dados = request.get_json()

    if not dados:
        return jsonify({
            "erro": "Login vazio"
        }), 400

    if "email" not in dados or "senha" not in dados:
        return jsonify({
            "erro": "Email e senha são obrigatorios"
        }), 400
    
    conexao = connect()
    cursor = conexao.cursor()

    try:
        cursor.execute("""
            SELECT * FROM usuarios
            WHERE email=?
        """, (dados["email"],))

        usuario = cursor.fetchone()

        if not usuario or usuario["senha"] != dados["senha"]:
            return jsonify({
                "erro": "Usuário ou senha inválidos"
            }), 401


        usuario_dict = dict(usuario)
        usuario_dict.pop("senha")

        token = create_access_token(
            identity=str(usuario_dict["id"])
        )

        return jsonify({
            "mensagem": "Login realizado com sucesso",
            "toke": token,
            "usuario": usuario_dict
        }), 200

    finally:
        conexao.close()