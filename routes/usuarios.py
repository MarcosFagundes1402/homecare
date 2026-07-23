from flask import jsonify, request, Blueprint
from database.connect import connect
import sqlite3

usuario_bp = Blueprint("usuarios", __name__)
usuario_logado = {
    "id": 1,
    "nome": "Lucas Seixas",
    "role": "ADMIN"
}

# CONSULTAR USUARIO (TODOS)
@usuario_bp.route('/usuarios', methods=['GET'])
def consultar_usuario():
    conexao = connect()
    cursor = conexao.cursor()

    cursor.execute("SELECT * FROM usuarios")

    usuarios = cursor.fetchall()

    lista_usuarios = []

    for usuario in usuarios:
        dados = dict(usuario)
        dados.pop("senha")
        lista_usuarios.append(dados)
    conexao.close()

    return jsonify(lista_usuarios),200

# CONSULTAR USUARIO POR (ID)
@usuario_bp.route('/usuarios/<int:id>', methods=['GET'])
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
def editar_usuarios(id):
    if usuario_logado.get("role") != "ADMIN":
        return jsonify({'erro': "Apenas ADMIN pode editar"}), 403
    
    usuario_editado = request.get_json()

    if not usuario_editado:
        return jsonify({
            "erro": "Dados não inseridos"
        }), 400

    conexao = connect()
    cursor = conexao.cursor()

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
            usuario_editado["senha"],
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
def atualizar_usuario_parcial(id):
    dados = request.get_json()

    conexao = connect()
    cursor = conexao.cursor()

    try:
        campos = []
        valores = []

        for campo, valor in dados.items():
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
def excluir_usuario(id):
    if usuario_logado.get("role") != "ADMIN":
            return jsonify({'erro': "Apenas ADMIN pode excluir"}), 403

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
def criar_usuario():
    if usuario_logado.get("role") != "ADMIN":
        return jsonify({
            'erro': 'Apenas ADMIN pode criar usuarios.'
        }), 403
    
    novo_usuario = request.get_json()

    if not novo_usuario:
        return jsonify({
            "erro": "Dados não enviados"
        }), 400

    conexao = connect()
    cursor = conexao.cursor()

    try:
        cursor.execute("""
            INSERT INTO usuarios (nome, email, role, senha)
            VALUES (?, ?, ?, ?)
        """,(
            novo_usuario["nome"],
            novo_usuario["email"],
            novo_usuario["role"],
            novo_usuario["senha"]
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