from flask import Blueprint, request, jsonify
from database.connect import connect
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash

from utils.response import validate_required_fields

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=['POST'])
def login():
    connection = None

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                    "erro": "Login vazio"
            }), 400

        required_fields = [
            "email",
            "senha"
        ]

        error = validate_required_fields(data, required_fields)

        if error:
            return jsonify({
                "erro": error
            }), 400

        connection = connect()
        cursor = connection.cursor()

        cursor.execute("""
             SELECT
                id,
                nome,
                email,
                senha,
                role
            FROM usuarios
            WHERE email = ?
        """, (
            data["email"],
        ))

        user = cursor.fetchone()

        if not user:
            return jsonify({
                "erro": "Usuário ou senha inválidos."
            }), 401

        if not check_password_hash(
            user["senha"],
            data["senha"],
        ):
            return jsonify({
                "erro": "Usuário ou senha inválidos."
            }), 401

        user_dict = dict(user)
        user_dict.pop("senha")

        token = create_access_token(
            identity=str(user_dict["id"])
        )

        return jsonify({
            "msg": "Login realizado com sucesso.",
            "token": token,
            "usuario": user_dict
        }), 200

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if connection:
            connection.close()