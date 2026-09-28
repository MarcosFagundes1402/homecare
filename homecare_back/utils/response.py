from flask import jsonify


def error_role(error, role_name, user=None):

    if error == "nao_encontrado":
        return jsonify({
            "erro": f"{role_name} não encontrado."
        }), 404

    if error == "role_invalida":
        response = {"erro": f"O usuário informado não é {role_name.lower()}."}

        if user:
            response["usuario"] = user["nome"]
            response["role"] = user["role"]

        return jsonify(response), 400

    return jsonify({
        "erro": "Erro de validação."
    }), 400

def validate_required_fields(data, required_fields):
    for field in required_fields:
        if (
            field not in data
            or data[field] is None
            or str(data[field]).strip() == ""
        ):
            return f"O campo '{field}' é obrigatório."

    return None

def validate_non_empty_field(data, fields):
    for field in fields:
        if field in data and (
            data[field] is None
            or str(data[field]).strip() == ""
        ):
            return f"O campo '{field}' não pode ser vazio."
        
    return None