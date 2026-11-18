from flask import jsonify, Blueprint
from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required,
    create_access_token,
)

refresh_bp = Blueprint("refresh", __name__, url_prefix="/refresh")

@refresh_bp.route("", methods=['POST'])
@jwt_required(refresh=True)

def refresh():
    user_id = get_jwt_identity()

    new_access_token = create_access_token(
        identity = user_id
    )

    return jsonify({
        "access_token": new_access_token
    }), 200
