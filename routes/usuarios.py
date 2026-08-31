from flask import jsonify, request, Blueprint
from database.connect import connect
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.permissoes import admin_required
from werkzeug.security import generate_password_hash

import sqlite3

usuario_bp = Blueprint("usuarios", __name__)

# CONSULTAR USUARIO (TODOS)
@usuario_bp.route('/usuarios/consultar', methods=['GET'])
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

    return jsonify(lista_usuarios), 200

# CONSULTAR USUARIO POR (ID)
@usuario_bp.route('/usuarios/consultar/<int:id>', methods=['GET'])
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

#REMOVI O PUT POIS ACHEI DESNECESSARIO TER QUE EDITAR TUDO É MAIS FACIL EDITAR ALGUMAS COISAS

# EDITAR USUARIO PARCIAL (ID)
@usuario_bp.route("/usuarios/editar/<int:id>", methods=['PATCH'])
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

            if valor is None or valor == "":
                return jsonify({
                    "erro": f"O campo '{campo}' não pode estar vazio."
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

        dados_retorno = {
            campo: valor
            for campo, valor in dados.items()
            if campo != "senha"
        }

        return jsonify ({
            "msg": "Usuário atualizado com sucesso.",
            "usuario": id,
            "dados_alterados": dados_retorno
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

# EXCLUIR USUARIO
@usuario_bp.route('/usuarios/deletar/<int:id>', methods=['DELETE'])
@jwt_required()
@admin_required()
def excluir_usuario(id):

    conexao = connect()
    cursor = conexao.cursor()

    try:
        #BUSCA O USUARIO E A ROLE E STATUS
        cursor.execute("""
            SELECT 
                u.role,
                p.status AS paciente_status,
                c.status AS cuidador_status 
            FROM usuarios u

            LEFT JOIN pacientes p 
                ON p.id = u.id

            LEFT JOIN cuidadores c  
                ON c.id = u.id
            WHERE u.id =?
        """, (id,))

        usuario = cursor.fetchone()

        if not usuario:
             return jsonify({
                 "erro": "Usuário não encontrado."
             }), 404
        
        role = usuario["role"].lower()

        #PEGA STATUS DEACORDO COM A ROLE
        if role == "paciente":
            status = usuario["paciente_status"]

        elif role == "cuidador":
            status = usuario["cuidador_status"]

        #SE FOR ADMIN NAO DESATIVA
        else:
            return jsonify({
                "erro": "Este tipo de usuário não pode ser desativado por esta rota."
            }), 400
        
        #VERIFICA SE JA ESTA INATIVO
        if status == "inativo":
            return jsonify({
                "erro": "Usuário já está inativo."
            }), 400

        #DESATIVAR PACIENTE
        if role == "paciente":
            cursor.execute("""
                UPDATE pacientes
                SET status = "inativo"
                WHERE id = ?
            """, (id,))

        #DESATIVAR CUIDADOR
        elif role == "cuidador":
            cursor.execute("""
                UPDATE cuidadores
                SET status = "inativo"
                WHERE id = ?
            """, (id,))

        
        conexao.commit()

        return jsonify({
            "msg": "Usuário desativado com sucesso.",
            "usuario_id": id,
            "role": role,
            "status": "inativo"
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
@jwt_required()
@admin_required()
def criar_usuario():

    novo_usuario = request.get_json()

    if not novo_usuario:
        return jsonify({
            "erro": "Dados não enviados"
        }), 400

    campos_obrigatorios = [
        "nome",
        "email",
        "senha",
        "role",
        "cpf",
        "data_nascimento",
        "tel",
        "endereco"
    ]

    #VERIFICA OS CAMPOS OBRIGATORIOS PARA VER SE NAO ESTA VAZIO
    for campo in campos_obrigatorios:
        if campo not in novo_usuario or not novo_usuario[campo]:
            return jsonify({
                "erro": f"o campo '{campo}' é obrigatório."
            }), 400

    role = novo_usuario["role"].lower()

    roles_permitidas = ["paciente", "cuidador"]

    if role not in roles_permitidas:
        return jsonify({
            "erro": "Role inválid. Ultilize paciente ou cuidador."
        }), 400


    conexao = None

    try:
        conexao = connect()
        cursor = conexao.cursor()

        senha_hash = generate_password_hash(novo_usuario["senha"])

        # CRIA USUARIO PRINCIPAL
        cursor.execute("""
            INSERT INTO usuarios (
                nome, 
                email, 
                role, 
                senha
            )
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
                novo_usuario["nome"],
                novo_usuario['cpf'],
                novo_usuario['data_nascimento'],
                novo_usuario['tel'],
                novo_usuario['endereco'],
                novo_usuario.get('obs'),
            ))

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
                novo_usuario.get('obs'),
                "ativo"
            ))

        conexao.commit()

        return jsonify({
            'msg': f'{role.capitalize()} inserido com sucesso.',
            'id': usuario_id
        }), 201

    except sqlite3.IntegrityError as e:
        if conexao:
            conexao.rollback()

        return jsonify({
            "erro": str(e)
        }), 400

    except Exception as e:
        if conexao: 
            conexao.rollback()

        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if conexao:
            conexao.close()
