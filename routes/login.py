from flask import Blueprint, request, jsonify
from database.connect import connect
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash

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
            "erro": "Email e senha são obrigatórios."
        }), 403

    conexao = connect()
    cursor = conexao.cursor()

    
    try:
        cursor.execute("""
            SELECT * FROM usuarios
            WHERE email=?
        """, (dados["email"],))

        usuario = cursor.fetchone()

        if not usuario:
            return jsonify({
                "erro": "Usuário ou senha inválidos"
            }), 401
        
        if not check_password_hash(usuario["senha"], dados["senha"]):
            return jsonify({
                "erro": "Usuáro ou senha inválidos"
            })

        usuario_dict = dict(usuario)
        usuario_dict.pop("senha")

        token = create_access_token(
            identity=str(usuario_dict["id"])
        )

        return jsonify({
            "mensagem": "Login realizado com sucesso",
            "token": token,
            "usuario": usuario_dict
        }), 200

    finally:
        conexao.close()