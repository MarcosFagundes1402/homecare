from flask import jsonify, request, Blueprint
from database.connect import connect
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.permissions import roles_required
from werkzeug.security import generate_password_hash, check_password_hash

from utils.response import validate_non_empty_fields, validate_required_fields

import sqlite3

user_bp = Blueprint("usuarios", __name__)

# CONSULTAR USUARIO (TODOS)
@user_bp.route('/usuarios/consultar', methods=['GET'])
@jwt_required()
@roles_required("admin")
def list_users():
    connection = None
    try:
        connection = connect()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                u.id,
                u.nome,
                u.email,
                u.role,

                CASE 
                    WHEN u.role = 'paciente' THEN p.status
                    WHEN u.role = 'cuidador' THEN c.status
                    WHEN u.role = 'admin' THEN 'ativo'
                    ELSE NULL
                END AS status

            FROM usuarios u

            LEFT JOIN pacientes p
                ON p.id = u.id
            
            LEFT JOIN cuidadores c
                ON  c.id = u.id
        """)

        users = cursor.fetchall()

        result = [dict(user) for user in users]

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500

    finally: 
        if connection:
            connection.close()


# CONSULTAR USUARIO POR (ID)
@user_bp.route('/usuarios/consultar/<int:id>', methods=['GET'])
@jwt_required()
@roles_required("admin")
def get_user_by_id(user_id):
    connection = None

    try:
        connection = connect()
        cursor = connection.cursor()

        cursor.execute("""
                SELECT
                    id,
                    nome,
                    email,
                    role
                FROM usuarios 
                WHERE id= ?
            """, (user_id,))

        user = cursor.fetchone()

        if not user:
            return jsonify({
                "erro": "Usuário não encontrado."
            }), 404

        return jsonify(dict(user)), 200

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if connection:
            connection.close()

#REMOVI O PUT POIS ACHEI DESNECESSARIO TER QUE EDITAR TUDO É MAIS FACIL EDITAR ALGUMAS COISAS

# EDITAR USUARIO PARCIAL (ID)
@user_bp.route("/usuarios/editar/<int:id>", methods=['PATCH'])
@jwt_required()
@roles_required("admin")
def update_user(user_id):
    connection = None


    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "erro": "Dados não enviados"
            }), 400
        
        connection = connect()
        cursor = connection.cursor()

        #BUSCA O USUÁRIO E A ROLE NO BANCO DE DADOS
        cursor.execute("""
            SELECT role
            FROM usuarios
            WHERE id = ?
        """, (user_id,))

        user = cursor.fetchone()

        if not user:
            return jsonify({
                "erro": "Usuário não encontrado."
            }), 404

        role = user["role"].lower()

        # CAMPOS QUE PODEM SER ALTERADOS
        allowed_fields = ["nome", "email", "senha"]

        for field in data:
            if field not in allowed_fields:
                return jsonify({
                    "erro": f"Campo '{field.upper()}' não pode ser alterado."
                }), 400

        error = validate_non_empty_fields(data, allowed_fields)

        if error:
            return jsonify({
                "erro": error
            }), 400
        
        fields = []
        values = []

        for field in allowed_fields:
            if field in data:
                value = data[field]

                if field == "senha":
                    value = generate_password_hash(value)

                fields.append(f"{field} = ?")
                values.append(value)

        if not fields:
             return jsonify({
                 "erro": "Nenhum campo válido foi enviado para edição."
             }), 400

        #VERIFICA DUPLICIDADE NO EMAIL ALTERADO
        if "email" in data:
            cursor.execute("""
                SELECT id
                FROM usuarios
                WHERE email =?
                AND id !=?
            """, (
                data["email"],
                user_id
            ))

            existing_email = cursor.fetchone()

            if existing_email:
                return jsonify({
                    "erro": "Email já utilizado por outro usuário."
                }), 400

        values.append(user_id)

        sql = f"""
            UPDATE usuarios 
            SET {', '.join(fields)}
            WHERE id=?
        """
        cursor.execute(sql, values)

        #SINCRONIZA O NOME NA TABELA 
        if "nome" in data:
            if role == "paciente":
                cursor.execute("""
                    UPDATE pacientes
                    SET nome =?
                    WHERE id =?
                """, (
                    data["nome"],
                    user_id
                ))

            elif role == "cuidador":
                cursor.execute("""
                    UPDATE cuidadores
                    SET nome =?
                    WHERE id =? 
                """, (
                    data["nome"], 
                    user_id
                ))

        connection.commit()

        return_data = {
            field: value
            for field, value in data.items()
            if field != "senha"
        }

        return jsonify ({
            "msg": "Usuário atualizado com sucesso.",
            "usuario": user_id,
            "data_alterados": return_data
        }), 200

    except sqlite3.IntegrityError as e:
        if connection:
            connection.rollback()

        return jsonify({
            "erro": str(e)
        }), 400

    except Exception as e:
        if connection:
            connection.rollback()

        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if connection:
            connection.close()

#DESATIVAR USUARIO
@user_bp.route('/usuarios/desativar/<int:id>', methods=['DELETE'])
@jwt_required()
@roles_required("admin")
def disable_user(user_id):
    connection = None

    try:
        connection = connect()
        cursor = connection.cursor()

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
        """, (user_id,))

        user = cursor.fetchone()

        if not user:
             return jsonify({
                 "erro": "Usuário não encontrado."
             }), 404
        
        role = user["role"].lower()

        #PEGA STATUS DE ACORDO COM A ROLE
        if role == "paciente":
            status = user["paciente_status"]

        elif role == "cuidador":
            status = user["cuidador_status"]


        #SE FOR ADMIN NAO DESATIVA
        else:
            return jsonify({
                "erro": "Este tipo de usuário não pode ser desativado por esta rota."
            }), 400
        
        if status is None:
            return jsonify({
                "erro": "Cadastro especifíco do usuário não encontrado."
            }), 404
        
        #VERIFICA SE JA ESTA INATIVO
        if status == "inativo":
            return jsonify({
                "erro": "Usuário já está inativo."
            }), 400

        #DESATIVAR PACIENTE
        if role == "paciente":
            cursor.execute("""
                UPDATE pacientes
                SET status = 'inativo'
                WHERE id = ?
            """, (user_id,))

        #DESATIVAR CUIDADOR
        elif role == "cuidador":
            cursor.execute("""
                UPDATE cuidadores
                SET status = 'inativo'
                WHERE id = ?
            """, (user_id,))
        
        connection.commit()

        return jsonify({
            "msg": "Usuário desativado com sucesso.",
            "user_id": user_id,
            "role": role,
            "status": 'inativo'
        }), 200

    except sqlite3.IntegrityError as e:
        if connection:
            connection.rollback()

        return jsonify({
            "erro": str(e)
        }), 400

    except Exception as e:
        if connection: 
            connection.rollback()

        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if connection:
            connection.close()

# CRIAR USUARIO
@user_bp.route("/usuarios/cadastro", methods=["POST"])
def register():
    new_user = request.get_json()

    if not new_user:
        return jsonify({
            "erro": "Dados não enviados."
        }), 400

    received_role = str(new_user.get("role", "")).strip().lower()

    required_fields = [
        "nome",
        "email",
        "senha",
        "confirmar_senha",
        "role"
    ]

    if received_role in ["paciente", "cuidador"]:
        required_fields += [
            "cpf",
            "data_nascimento",
            "tel",
            "endereco"
        ]

    error = validate_required_fields(new_user, required_fields)

    if error:
        return jsonify({
            "erro": error
        }), 400

    if new_user["senha"] != new_user["confirmar_senha"]:
        return jsonify({
            "erro": "As senhas não coincidem."
        }), 400

    role = received_role

    allowed_roles = ["admin", "paciente", "cuidador"]

    if role not in allowed_roles:
        return jsonify({
            "erro": "Função inválida."
        }), 400

    connection = None

    try:
        connection = connect()
        cursor = connection.cursor()

        password_hash = generate_password_hash(
            new_user["senha"]
        )

        cursor.execute("""
            INSERT INTO usuarios (
                nome,
                email,
                role,
                senha
            )
            VALUES (?, ?, ?, ?)
        """, (
            new_user["nome"],
            new_user["email"].strip().lower(),
            role,
            password_hash
        ))

        user_id = cursor.lastrowid

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
                user_id,
                new_user["nome"],
                new_user["cpf"],
                new_user["data_nascimento"],
                new_user["tel"],
                new_user["endereco"],
                new_user.get("obs"),
            ))

        elif role == "cuidador":
            cursor.execute("""
                INSERT INTO cuidadores (
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
                user_id,
                new_user["nome"],
                new_user["cpf"],
                new_user["data_nascimento"],
                new_user["tel"],
                new_user["endereco"],
                new_user.get("obs"),
            ))

        connection.commit()

        return jsonify({
            "msg": f"{role.capitalize()} cadastrado com sucesso.",
            "id": user_id
        }), 201

    except sqlite3.IntegrityError as e:
        if connection:
            connection.rollback()

        return jsonify({
            "erro": str(e)
        }), 400

    except Exception as e:
        if connection:
            connection.rollback()

        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if connection:
            connection.close()

@user_bp.route('/usuarios/criar', methods=['POST'])
@jwt_required()
@roles_required("admin")
def create_user():

    new_user = request.get_json()

    if not new_user:
        return jsonify({
            "erro": "Dados não enviados."
        }), 400

    received_role = str(new_user.get("role", "")).strip().lower()

    required_fields = [
        "nome",
        "email",
        "senha",
        "confirmar_senha",
        "role"
    ]

    if received_role in ["paciente", "cuidador"]:
        required_fields += [
            "cpf",
            "data_nascimento",
            "tel",
            "endereco"
        ]

    error = validate_required_fields(new_user, required_fields)

    if error:
        return jsonify({
            "erro": error
        }), 400

    #VALIDA SE AS SENHA SÃO IGUAIS
    if new_user ["senha"] != new_user ["confirmar_senha"]:
        return jsonify({
            "erro": "As senhas não coincidem."
        }), 400

    role = received_role

    allowed_roles = ["admin", "paciente", "cuidador"]

    if role not in allowed_roles:
        return jsonify({
            "erro": "Função inválida. Utilize paciente ou cuidador."
        }), 400

    connection = None

    try:
        connection = connect()
        cursor = connection.cursor()

        password_hash = generate_password_hash(new_user["senha"])

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
            new_user["nome"],
            new_user["email"].strip().lower(),
            role,
            password_hash
        ))

        user_id = cursor.lastrowid

        # SE FOR PACIENTE, CRIA O PERFIL DE PACIENTE
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
                user_id,
                new_user["nome"],
                new_user['cpf'],
                new_user['data_nascimento'],
                new_user['tel'],
                new_user['endereco'],
                new_user.get('obs'),
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
                        obs
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                user_id,
                new_user['nome'],
                new_user['cpf'],
                new_user['data_nascimento'],
                new_user['tel'],
                new_user['endereco'],
                new_user.get('obs'),
            ))

        connection.commit()

        return jsonify({
            'msg': f'{role.capitalize()} inserido com sucesso.',
            'id': user_id
        }), 201

    except sqlite3.IntegrityError as e:
        if connection:
            connection.rollback()

        return jsonify({
            "erro": str(e)
        }), 400

    except Exception as e:
        if connection: 
            connection.rollback()

        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if connection:
            connection.close()

#ROTA ESQUECI SENHA
@user_bp.route("/usuarios/esqueci-senha", methods=['POST'])
def forgot_password():
    data = request.get_json()

    if not dados or not dados.get("email", "").strip():
        return jsonify({
            "erro": "E-mail é obrigatório"
        }), 400

    email = dados["email"].strip()

    conexao = connect()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT id, email
        FROM usuarios 
        WHERE email = ?
    """, (email,))

    usuario = cursor.fetchone()

    conexao.close()

    conexao.close()

    if not usuario:
        return jsonify({
            "erro": "E-mail não encontrado"
        }), 404

    return jsonify({
        "msg": "E-mail encontrado"
    }), 200

#ALTERAR SENHA
@user_bp.route("/usuarios/alterar-senha", methods=['PATCH'])
@jwt_required()
def change_password():
    connection = None

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "erro": "Dados não encontrados."
            }), 400

        required_fields = [
            "senha_atual",
            "nova_senha",
            "confirmar_senha"
        ]

        error = validate_required_fields(data, required_fields)

        if error:
            return jsonify({
                "erro": error
            }), 400

        #VERIFICA SE AS SENHAS SÃO IGUAIS
        if data["nova_senha"] != data["confirmar_senha"]:
            return jsonify({
                "erro": "As senhas não coincidem."
            }), 400
        
        user_id = int(get_jwt_identity())

        connection = connect()
        cursor = connection.cursor()

        #BUSCA USUARIO E A SENHA ATUAL
        cursor.execute("""
            SELECT
                id,
                nome,
                senha
            FROM usuarios
            WHERE id = ?
        """, (user_id,))

        user = cursor.fetchone()

        if not user:
            return jsonify({
                "erro": "Usuário não encontrado."
            }), 404

        #CONFERE SENHA ATUAL
        if not check_password_hash(
            user["senha"],
            data["senha_atual"]
        ):
            return jsonify({
                "erro": "Senha atual incorreta."
            }), 400

        #EVITAR DUPLICIDADE DE SENHA
        if check_password_hash (
            user["senha"],
            data["nova_senha"]
        ):
            return jsonify({
                "erro": "A nova senha não pode ser igual à senha atual."
            }), 400

        #GERA O HASH DA NOVA SENHA
        new_password_hash = generate_password_hash(data["nova_senha"])

        #ATUALIZA A SENHA
        cursor.execute("""
            UPDATE usuarios
            SET senha = ?
            WHERE id = ?
        """, (
            new_password_hash,
            user_id
        ))

        connection.commit()

        return jsonify({
            "msg": "Senha alterada com sucesso."
        }), 200

    except Exception as e:
        if connection:
            connection.rollback()

        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if connection:
            connection.close()
