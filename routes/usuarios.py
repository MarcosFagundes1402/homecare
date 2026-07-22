from flask import Flask, jsonify, request
from database.connect import connect

app = Flask(__name__)

usuarios = [
    {
        "id": 1,
        "nome": "Lucas Seixas",
        "email": "lucas@careplus.com",
        "senha": "123456",
        "role": "ADMIN"
    },
    {
        "id": 2,
        "nome": "Marcos Fagundes",
        "email": "marcos@careplus.com",
        "senha": "123456",
        "role": "CUIDADOR"
    },
    {
        "id": 3,
        "nome": "Ana Souza",
        "email": "ana@email.com",
        "senha": "123456",
        "role": "CUIDADOR"
    },
    {
        "id": 4,
        "nome": "Carlos Pereira",
        "email": "carlos@email.com",
        "senha": "123456",
        "role": "FAMILIAR"
    },
    {
        "id": 5,
        "nome": "Maria Aparecida",
        "email": "maria@email.com",
        "senha": "123456",
        "role": "PACIENTE"
    }
]

usuario_logado = {
        "id": 1,
        "nome": "Lucas Seixas",
        "email": "lucas@careplus.com",
        "senha": "123456",
        "role": "ADMIN"
    }

# CONSULTAR USUARIO (TODOS)
@app.route('/usuarios', methods=['GET'])
def obter_users():
    return jsonify(usuarios)

# CONSULTAR USUARIO POR (ID)
@app.route('/usuarios/<int:id>', methods=['GET'])
def obter_users_id(id):
    for user in usuarios:
        if user.get('id') == id:
            return jsonify(user)
    return jsonify({"erro": "Usuarios nao encontrado"})
        
# EDITAR USUARIO
@app.route('/usuarios/<int:id>', methods=['PUT'])
def editar_usuarios(id):
    if usuario_logado.get("role") != "ADMIN":
        return jsonify({'erro': "Apenas ADMIN pode editar"}), 403
    
    usuario_editado = request.get_json()

    for user in usuarios:
        if user.get("id") == id:
            user.update(usuario_editado)
            return jsonify(user)
    return jsonify({'erro': 'Usuario nao encontrado'}), 404

# EXCLUIR USUARIO
@app.route('/usuarios/<int:id>', methods=['DELETE'])
def excluir_usuario(id):

    if usuario_logado.get("role") != "ADMIN":
        return jsonify({'erro': "Apenas ADMIN pode excluir"}), 403
    
    for indice,user in enumerate(usuarios):

        if user['id'] == id:
            del usuarios[indice]
            
            return jsonify({
                "menssagem": "Usuario excluido com sucesso!"
            }), 200
    
    return jsonify({
        "erro": "Usuario nao encontrado"
    }), 404

# CRIAR USUARIO
@app.route('/usuarios', methods=['POST'])
def criar_usuario():
    if usuario_logado.get("role") != "ADMIN":
        return jsonify({
            'erro': 'Apenas ADMIN pode criar usuarios.'
        }), 403
    
    novo_usuario = request.get_json()
    novo_usuario['id'] = len(usuarios) + 1
    usuarios.append(novo_usuario)

    return jsonify(novo_usuario), 201

app.run(port=5000, host='localhost', debug=True)