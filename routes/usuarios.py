from flask import jsonify, request, Blueprint
from database.connect import connect
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.permissoes import admin_required
from werkzeug.security import generate_password_hash

import sqlite3

usuario_bp = Blueprint("usuarios", __name__)

# CONSULTAR USUARIO (TODOS)
@usuario_bp.route('/usuarios', methods=['GET'])
@jwt_required()
@admin_required()
def consultar_usuario():

    conexao = connect()
    cursor = conexao.cursor()

    cursor.execute("SELECT * FROM usuarios")

    usuarios = cursor.fetchall()

    lista_usuarios = []

    for usuario in usuarios:
        dados = dict(usuario)
        dados.pop("senha", None)
        lista_usuarios.append(dados)
    conexao.close()

    return jsonify(lista_usuarios),200

# CONSULTAR USUARIO POR (ID)
@usuario_bp.route('/usuarios/<int:id>', methods=['GET'])
@jwt_required()
@admin_required()
def consultar_usuario_id(id):
    
    conexao = connect()
    cursor = conexao.cursor()

    cursor.execute(""" SELECT * FROM usuarios WHERE id= ?""", (id,))

    usuario = cursor.fetchone()    
    conexao.close()

    if usuario:
        dados = dict(usuario)
        dados.pop("senha")

        return jsonify(dados), 200
    
    return jsonify({
        "erro": "Usuário não encontrado"
    }), 404
        
# EDITAR USUARIO TOTAL
@usuario_bp.route('/usuarios/<int:id>', methods=['PUT'])
@jwt_required()
@admin_required()
def editar_usuarios(id):
    
    usuario_editado = request.get_json()

    if not usuario_editado:
        return jsonify({
            "erro": "Dados não inseridos"
        }), 400

    conexao = connect()
    cursor = conexao.cursor()

    senha_hash = generate_password_hash(usuario_editado["senha"])
    try:
        cursor.execute("""
            SELECT id FROM usuarios
            WHERE email =? AND id !=?
        """,(
            usuario_editado["email"],
            id
        ))

        email_existente = cursor.fetchone()
        if email_existente:
            return jsonify({
                "erro": "Email já utilizado por outro usuário"
            }), 400

        cursor.execute("""
            UPDATE usuarios
            SET nome=?, email=?, role=?, senha=?
            WHERE id=?
        """,( 
            usuario_editado["nome"],
            usuario_editado["email"],
            usuario_editado["role"],
            senha_hash,
            id
        ))

        conexao.commit()

        if cursor.rowcount == 0:
            return jsonify({
                "erro": "Usuário não encontrado"
            }), 404
        return jsonify({ 
            "mensagem": "Usuário atualizado com sucesso"
        }), 200
    except sqlite3.IntegrityError:
        return jsonify({
            "erro": "Email já cadastrado"
        }), 400
    
    finally:
        conexao.close()

# EDITAR USUARIO PARCIAL (ID)
@usuario_bp.route("/usuarios/<int:id>", methods=['PATCH'])
@jwt_required()
@admin_required()
def atualizar_usuario_parcial(id):
    
    dados = request.get_json()

    conexao = connect()
    cursor = conexao.cursor()

    try:
        campos = []
        valores = []

        for campo, valor in dados.items():
            if campo == "senha":
                valor = generate_password_hash(valor)

            campos.append(f"{campo}=?")
            valores.append(valor)

        valores.append(id)

        sql = f"""
            UPDATE usuarios 
            SET {', '.join(campos)}
            WHERE id=?
        """
        cursor.execute(sql, valores)

        conexao.commit()

        if cursor.rowcount == 0:
            return jsonify({
                "erro": "Usuário não encontrado"
            }), 404

        return jsonify({
            "mensagem": "Usuário atualizado"
        }), 200
    finally:
        conexao.close()

# EXCLUIR USUARIO
@usuario_bp.route('/usuarios/<int:id>', methods=['DELETE'])
@jwt_required()
@admin_required()
def excluir_usuario(id):

    conexao = connect()
    cursor = conexao.cursor()

    try:
        cursor.execute("""
            DELETE FROM usuarios
            WHERE id=?
        """,(id,))

        conexao.commit()

        if cursor.rowcount == 0:
            return jsonify({
                "erro": "Usuário não encontrado"
            }), 404
        return jsonify({ 
            "mensagem": "Usuário excluído com sucesso."
        }), 200

    finally:
        conexao.close()

        
# CRIAR USUARIO
@usuario_bp.route('/usuarios', methods=['POST'])
@jwt_required()
@admin_required()
def criar_usuario():
    
    novo_usuario = request.get_json()

    if not novo_usuario:
        return jsonify({
            "erro": "Dados não enviados"
        }), 400

    conexao = connect()
    cursor = conexao.cursor()

    senha_hash = generate_password_hash(novo_usuario["senha"])

    try:
        cursor.execute("""
            INSERT INTO usuarios (nome, email, role, senha)
            VALUES (?, ?, ?, ?)
        """,(
            novo_usuario["nome"],
            novo_usuario["email"],
            novo_usuario["role"],
            senha_hash
        ))
        conexao.commit()

        return jsonify({"mensagem": "Usuario inserido com sucesso"}), 201
    
    except sqlite3.IntegrityError:
        return jsonify({"mensagem": "Erro: Email ja cadastrado"}), 400
    
    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500
    
    finally:
        conexao.close()