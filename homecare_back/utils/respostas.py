from flask import jsonify


def erro_role(erro, role_nome, usuario=None):

    if erro == "nao_encontrado":
        return jsonify({
            "erro": f"{role_nome} não encontrado."
        }), 404

    if erro == "role_invalida":
        resposta = {"erro": f"O usuário informado não é {role_nome.lower()}."}

        if usuario:
            resposta["usuario"] = usuario["nome"]
            resposta["role"] = usuario["role"]

        return jsonify(resposta), 400

    return jsonify({
        "erro": "Erro de validação."
    }), 400
