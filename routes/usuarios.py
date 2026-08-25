from flask import jsonify, request, Blueprint
from database.connect import connect
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.permissoes import admin_required
from werkzeug.security import generate_password_hash

import sqlite3

usuario_bp = Blueprint("usuarios", __name__)

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
        dados.pop("senha", None)
        lista_usuarios.append(dados)
    conexao.close()

    return jsonify(lista_usuarios), 200

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
        #BUSCAR ROLE DIRETO DO BANCO DE DADOS
        cursor.execute("""
            SELECT role
            FROM usuarios
            WHERE id = ?
        """,(id,))

        usuario = cursor.fetchone()

        if not usuario:
            return jsonify({
                "erro": "Usuário não encontrado"
            }), 404

        role = usuario["role"].lower()

        # VERIFICA SE O EMAIL JÁ ESTÁ SENDO USADO
        cursor.execute("""
            SELECT id
            FROM usuarios
            WHERE email =?
            AND id !=?
        """, (
            usuario_editado["email"],
            id
        ))

        email_existente = cursor.fetchone()

        if email_existente:
            return jsonify({
                "erro": "Email já utilizado por outro usuário"
            }), 400

        # ATUALIZA TABELA USUARIOS
        cursor.execute("""
            UPDATE usuarios
            SET nome=?, email=?, senha=?
            WHERE id=?
        """, (
            usuario_editado["nome"],
            usuario_editado["email"],
            senha_hash,
            id
        ))

        if cursor.rowcount == 0:
            return jsonify({
                "erro": "Usuário não encontrado"
            }), 404

        # SINCRONIZA O NOME NA TABELA PACIENTES
        if role == "paciente":
            cursor.execute("""
                UPDATE pacientes
                SET nome =?
                WHERE id =?
            """, (
                    usuario_editado["nome"],
                    id
                ))

        elif role == "cuidador":
            cursor.execute("""
                UPDATE cuidadores
                SET nome =?
                WHERE id =?
            """, (
                    usuario_editado["nome"],
                    id
                ))
            
        conexao.commit()

        return jsonify({
            "mensagem": "Usuário atualizado com sucesso"
        }), 200

    except sqlite3.IntegrityError as e:
        conexao.rollback()

        return jsonify({
            "erro": str(e)
        }), 400

    except Exception as e:
        conexao.rollback()

        return jsonify({
            "erro": str(e)
        }), 500
    
    finally:
        conexao.close()

# EDITAR USUARIO PARCIAL (ID)
@usuario_bp.route("/usuarios/<int:id>", methods=['PATCH'])
@jwt_required()
@admin_required()
def atualizar_usuario_parcial(id):

    dados = request.get_json()

    if not dados:
        return jsonify({
            "erro": "Dados não enviados"
         }), 400

    conexao = connect()
    cursor = conexao.cursor()

    try:
        #BUSCA O USUÁRIO E A ROLE NO BANCO DE DADOS
        cursor.execute("""
            SELECT role
            FROM usuarios
            WHERE id = ?
        """, (id,))

        usuario = cursor.fetchone()

        if not usuario:
            return jsonify({
                "erro": "Usuário não encontrado."
            }), 404

        role = usuario["role"].lower()

        # CAMPOS QUE PODEM SER ALTERADOS
        campos_permitidos = ["nome", "email", "senha"]

        campos = []
        valores = []

        for campo, valor in dados.items():
            if campo not in campos_permitidos:
                return jsonify({
                    "erro": f"Campo '{campo.upper()}' não pode ser alterado."
                }), 400
            
            if campo == "senha":
                valor = generate_password_hash(valor)

            campos.append(f"{campo} = ?")
            valores.append(valor)

        #VERIFICA DUPLICIDADE NO EMAIL ALTERADO
        if "email" in dados:
            cursor.execute("""
                SELECT id
                FROM usuarios
                WHERE email =?
                AND id !=?
            """, (
                dados["email"],
                id
            ))

            email_existente = cursor.fetchone()

            if email_existente:
                return jsonify({
                    "erro": "Email já utilizado por outro usuário."
                }), 400

        valores.append(id)

        sql = f"""
            UPDATE usuarios 
            SET {', '.join(campos)}
            WHERE id=?
        """
        cursor.execute(sql, valores)

        #SINCRONIZA O NOME NA TABELA 
        if "nome" in dados:
            if role == "paciente":
                cursor.execute("""
                    UPDATE pacientes
                    SET nome =?
                    WHERE id =?
                """, (
                    dados["nome"],
                    id
                ))

            elif role == "cuidador":
                cursor.execute("""
                    UPDATE cuidadores
                    SET nome =?
                    WHERE id =? 
                """, (
                    dados["nome"], 
                    id
                ))

        conexao.commit()

        return jsonify ({
            "msg": "Usuário atualizado com sucesso."
        }),200

    except sqlite3.IntegrityError as e:
        conexao.rollback()

        return jsonify({
            "erro": str(e)
        }), 400

    except Exception as e:
        conexao.rollback()

        return jsonify({
            "erro": str(e)
        }), 500

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
        #BUSCA O USUARIO E A ROLE
        cursor.execute("""
            SELECT role 
            FROM usuarios
            WHERE id =?
        """, (id,))

        usuario = cursor.fetchone()

        if not usuario:
             return jsonify({
                 "erro": "Usuário não encontrado."
             }), 404
        
        role = usuario["role"].lower()

        #SE FOR PACIENTE
        if role == "paciente":

            #REMOVE OS VINCULOS COM CUIDADORES
            cursor.execute("""
                DELETE FROM cuidadores_pacientes
                WHERE paciente_id =?
            """, (id,))

            #REMOVE O PERFIL DE PACIENTE
            cursor.execute("""
                DELETE FROM pacientes
                WHERE id =?
            """, (id,))

        #SE FOR CUIDADOR
        elif role == "cuidador":

            #REMOVE OS VINCULOS COM PACIENTES
            cursor.execute("""
                DELETE FROM cuidadores_pacientes
                WHERE cuidador_id =?
            """, (id,))

            #REMOVE PERFIL DE CUIDADOR
            cursor.execute("""
                DELETE FROM cuidadores
                WHERE id =?
            """, (id,))

        #REMOVE O USUARIO
        cursor.execute("""
            DELETE FROM usuarios
            WHERE id=?
        """, (id,))

        conexao.commit()

        return jsonify({
            "msg": "Usuário excluído com sucesso."
        }), 200

    except sqlite3.IntegrityError as e:
        conexao.rollback()

        return jsonify({
            "erro": str(e)
        }), 400

    except Exception as e:
        conexao.rollback()

        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        conexao.close()

# CRIAR USUARIO
@usuario_bp.route('/usuarios/criar', methods=['POST'])
def criar_usuario():

    novo_usuario = request.get_json()

    if not novo_usuario:
        return jsonify({
            "erro": "Dados não enviados"
        }), 400

    role = novo_usuario['role'].lower()

    conexao = connect()
    cursor = conexao.cursor()

    senha_hash = generate_password_hash(novo_usuario["senha"])

    try:
        # CRIA USUARIO PRINCIPAL
        cursor.execute("""
            INSERT INTO usuarios (nome, email, role, senha)
            VALUES (?, ?, ?, ?)
        """, (
            novo_usuario["nome"],
            novo_usuario["email"],
            role,
            senha_hash
        ))

        usuario_id = cursor.lastrowid

        # SE FOR PACIENTEM CRIA O PERFIL DE PACIENTE
        if role == "paciente":
            cursor.execute("""
                INSERT INTO pacientes (
                    id,
                    nome,
                    cpf,
                    data_nascimento,
                    tel,
                    endereco,
                    obs
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                usuario_id,
                novo_usuario['nome'],
                novo_usuario['cpf'],
                novo_usuario['data_nascimento'],
                novo_usuario['tel'],
                novo_usuario['endereco'],
                novo_usuario['obs']
            ))

            conexao.commit()

            return jsonify({
                'msg': 'Paciente inserido com sucesso',
                'id': usuario_id
            }), 201

        elif role == 'cuidador':
            cursor.execute("""
                INSERT INTO cuidadores (
                        id,
                        nome,
                        cpf,
                        data_nascimento,
                        tel,
                        endereco,
                        obs,
                        status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                usuario_id,
                novo_usuario['nome'],
                novo_usuario['cpf'],
                novo_usuario['data_nascimento'],
                novo_usuario['tel'],
                novo_usuario['endereco'],
                novo_usuario['obs'],
                novo_usuario['status']
            ))

            conexao.commit()

            return jsonify({
                'msg': 'Cuidador inserido com sucesso.',
                'id': usuario_id
            }), 201

        conexao.commit()

        return jsonify({
            'msg': f'{role.capitalize()} inserido com sucesso.',
            'id': usuario_id
        }), 201

    except sqlite3.IntegrityError as e:
        conexao.rollback()

        return jsonify({
            "erro": str(e)
        }), 400

    except Exception as e:
        conexao.rollback()

        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        conexao.close()
