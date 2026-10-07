from flask import Blueprint, request, jsonify
from database.connect import connect
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash
from utils import get_user_by_email

from utils.response import validate_required_fields

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=['POST'])
def login():
    connection = None

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                    "error": "Login vazio"
            }), 400

        required_fields = [
            "email",
            "password"
        ]

        error = validate_required_fields(data, required_fields)

        if error:
            return jsonify({
                "error": error
            }), 400

        connection = connect()
        cursor = connection.cursor()

        # BUSCA USUARIO PELO EMAIL
        user = get_user_by_email(cursor, data["email"])

        if not user:
            return jsonify({
                "error": "Usuário ou senha inválidos."
            }), 401

        if not user['active']:
            return jsonify({
                "error": "Usuário inativo. Entre em contato com o administrador."
            }), 403

        if not check_password_hash(
            user["password_hash"],
            data["password"],
        ):
            return jsonify({
                "error": "Usuário ou senha inválidos."
            }), 401

        user_dict = dict(user)
        user_dict.pop("password_hash")

        token = create_access_token(
            identity=str(user_dict["id"])
        )

        return jsonify({
            "message": "Login realizado com sucesso.",
            "token": token,
            "user": user_dict
        }), 200

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

    finally:
        if connection:
            connection.close()