from flask import Blueprint, jsonify, request
from database.connect import connect
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.permissoes import admin_required, roles_required

medicamentos_bp = Blueprint("medicamentos",__name__)

#CRIA MEDICAMENTO PARA UM PACIENTE
@medicamentos_bp.route("/medicamentos/criar", methods=['POST'])
@jwt_required()
@admin_required()
def criar_medicamentos():
    conexao = None

    try:
        dados = request.get_json()

        if not dados:
            return jsonify({
                "erro": "Dados não encontrados."
            }), 400

        campos_obrigatorios = [
                    "paciente_id",
                    "nome",
                    "dosagem",
                    "horario"
                ]
        
        for campo in campos_obrigatorios:
            if campo not in dados or dados[campo] is None or dados[campo] == "":
                return jsonify({
                    "erro": f"O campo '{campo}' é obrigatório."
                }), 400

        conexao = connect()
        cursor = conexao.cursor()

        #VERIFICA SE O PACIENTE EXISTE
        cursor.execute("""
            SELECT
                pacientes.id,
                pacientes.nome,
                pacientes.status,
                usuarios.role
            FROM pacientes

            JOIN usuarios
                ON pacientes.id = usuarios.id

            WHERE pacientes.id = ?
        """,(
            dados["paciente_id"],
        ))

        paciente = cursor.fetchone()

        if not paciente:
            return jsonify({
                "erro": "Paciente não encontrado."
            }), 404
        
        #VERIFICA SE É PACIENTE
        if paciente["role"].lower() != "paciente":
            return jsonify({
                "erro": "O ID informado não pertence a um paciente.",
            }), 400

        #VERIFICA SE PACIENTE ESTA ATIVO
        if paciente["status"] != "ativo":
            return jsonify({
                "erro": "Não é possível cadastrar medicamento para paciente inativo."
            }), 400
        
        #CRIA O MEDICAMENTO
        cursor.execute("""
            INSERT INTO medicamentos(
                paciente_id,
                nome,
                dosagem,
                horario,
                obs,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """,(
            dados["paciente_id"],
            dados["nome"],
            dados.get("dosagem"),
            dados.get("horario"),
            dados.get("obs"),
            dados.get("status", "ativo")
        ))

        medicamento_id = cursor.lastrowid

        conexao.commit()

        return jsonify({
            "msg": "Medicamento criado com sucesso.",

            "paciente": {
                "id": paciente["id"],
                "nome": paciente["nome"]
            },

            "medicamento":{
                "id": medicamento_id,
                "nome": dados["nome"],
                "dosagem": dados.get("dosagem"),
                "horario": dados.get("horario"),
                "obs": dados.get("obs"),
                "status": dados.get("status", "ativo")
            }
        }), 201

    except Exception as e:
        if conexao:
            conexao.rollback()

        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if conexao:
            conexao.close()

# ADMIN CONSULTAR MEDICAMENTOS DE UM PACIENTE
@medicamentos_bp.route("/medicamentos/consultar/<int:id>", methods=['GET'])
@jwt_required()
@admin_required()
def listar_medicamentos_paciente(id):
    conexao = None

    try:
        conexao = connect()
        cursor = conexao.cursor()

        # VERIFICA SE O PACIENTE EXISTE
        cursor.execute("""
            SELECT 
                pacientes.id,
                pacientes.nome,
                usuarios.role
            FROM pacientes
            JOIN usuarios
                ON pacientes.id = usuarios.id
            WHERE pacientes.id = ?
        """, (id,))

        paciente = cursor.fetchone()

        if not paciente:
            return jsonify({
                "erro": "Paciente não encontrado."
            }), 404

        # VERIFICA SE REALMENTE É PACIENTE
        if paciente["role"].lower() != "paciente":
            return jsonify({
                "erro": "O ID informado não pertence a um paciente."
            }), 400

        # BUSCA O MEDICAMENTO DO PACIENTE
        cursor.execute("""
            SELECT 
                id,
                nome,
                dosagem,
                horario,
                obs,
                status
            FROM medicamentos
            WHERE paciente_id = ?
            ORDER BY id DESC
        """, (id,))

        medicamentos = cursor.fetchall()

        if not medicamentos:
            return jsonify({
                "msg": "Este paciente não possui medicamentos cadastrados."
            }), 200

        lista_medicamento = [dict(medicamento) for medicamento in medicamentos]

        return jsonify({
            "paciente": {
                "id": paciente["id"],
                "nome": paciente["nome"]
            },
            "medicamentos": lista_medicamento
        }), 200

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if conexao:
            conexao.close()


#PACIENTE CONSULTA OS PROPRIOS MEDICAMENTOS
@medicamentos_bp.route("/medicamentos/meus-medicamentos", methods=['GET'])
@jwt_required()
@roles_required("paciente")
def meus_medicamentos():
    conexao = None

    try:
        paciente_id = int(get_jwt_identity())

        conexao = connect()
        cursor = conexao.cursor()

        #BUSCA PACIENTE LOGADO
        cursor.execute("""
            SELECT id, nome
            FROM usuarios
            WHERE id = ?
        """, (paciente_id,))

        paciente = cursor.fetchone()

        if not paciente:
            return jsonify({
                "erro": "Paciente não encontrado."
            }), 404

        #BUSCA O MEDICAMENTO DO PACIENTE
        cursor.execute("""
            SELECT 
                id,
                nome,
                dosagem,
                horario,
                obs,
                status
            FROM medicamentos
            WHERE paciente_id = ?
            ORDER BY id DESC
        """, (paciente_id,))

        medicamentos = cursor.fetchall()

        if not medicamentos:
            return jsonify({
                "msg": "Você não possui medicamentos cadastrados."
            }), 200

        lista_medicamento = [dict(medicamento) for medicamento in medicamentos]

        return jsonify({
            "paciente":{
                "id": paciente["id"],
                "nome": paciente["nome"]
            },
            "medicamentos": lista_medicamento
        }), 200

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if conexao:
            conexao.close()

#CUIDADOR VERIFICA OS MEDICAMENTOS DO SEUS PACIENTES
@medicamentos_bp.route("/medicamentos/meus-pacientes", methods=['GET'])
@jwt_required()
@roles_required("cuidador")
def meus_pacientes():
    conexao = None

    try:
        cuidador_id = int(get_jwt_identity())

        conexao = connect()
        cursor = conexao.cursor()

        #BUSCA CUIDADOR LOGADO
        cursor.execute("""
            SELECT id, nome
            FROM usuarios
            WHERE id = ?
        """, (cuidador_id,))

        cuidador = cursor.fetchone()

        if not cuidador:
            return jsonify({
                "erro": "Cuidador não encontrado."
            }), 404

        #BUSCAR OS MEDICAMENTOS DOS PACIENTES VINCULADOS
        cursor.execute("""
            SELECT 
                m.id,
                m.nome,
                m.dosagem,
                m.horario,
                m.obs,
                m.status,

                p.id AS paciente_id,
                p.nome AS paciente_nome
            
            FROM medicamentos m

            JOIN cuidadores_pacientes cp
                ON cp.paciente_id = m.paciente_id
            
            JOIN usuarios p
                ON p.id = m.paciente_id
            
            WHERE cp.cuidador_id = ?

            ORDER BY p.nome, m.id DESC
        """, (cuidador_id,))        

        medicamentos = cursor.fetchall()

        if not medicamentos:
            return jsonify({
                "msg": "Seus pacientes não possuem medicamentos cadastrados."
            }), 200

        lista_medicamentos = []

        for medicamento in medicamentos:
            lista_medicamentos.append({
                "id": medicamento["id"],
                "nome": medicamento["nome"],
                "dosagem": medicamento["dosagem"],
                "horario": medicamento["horario"],
                "obs": medicamento["obs"],
                "status": medicamento["status"],

                "paciente": {
                    "id": medicamento["paciente_id"],
                    "nome": medicamento["paciente_nome"]
                }
            })

        return jsonify({
            "cuidador": {
                "id": cuidador["id"],
                "nome": cuidador["nome"]
            },

            "medicamentos": lista_medicamentos
        }), 200

    except Exception as e:

        return jsonify({
            "erro": str(e)
        }), 500
    
    finally:
        if conexao:
            conexao.close()
        
#EDITA UM MEDICAMENTO
@medicamentos_bp.route("/medicamentos/<int:id>", methods=['PATCH'])
@jwt_required()
@admin_required()
def editar_medicamento(id):
    conexao = None

    try:
        dados = request.get_json()

        if not dados:
            return jsonify({
                "erro": "Dados não encontrados."
            }), 400

        conexao = connect()
        cursor = conexao.cursor()

        #VERIFICA SE O MEDICAMENTO EXISTE
        cursor.execute("""
            SELECT id, paciente_id, nome
            FROM medicamentos
            WHERE id =?
        """,(id,))

        medicamento = cursor.fetchone()

        if not medicamento:
            return jsonify({
                "erro": "Medicamento não encontrado."
            }), 404

        #CAMPOS QUE PODE SER EDITADOS
        campos_permitidos = [
            "nome",
            "dosagem",
            "horario",
            "obs",
            "status"
        ]

        #VERIFICA SE FOI ENVIADO CAMPO NAO PERMITIDO
        for campo in dados:
            if campo not in campos_permitidos:
                return jsonify({
                    "erro": f"O campo '{campo}' não pode ser editado."
                }), 400

        #CAMPOS NAO PODEM FICAR VAZIOS
        campos_obrigatorios = [
            "nome",
            "dosagem",
            "horario"
        ]

        for campo in campos_obrigatorios:
            if campo in dados and (dados[campo] is None or dados[campo] == ""):
                return jsonify({
                    "erro": f"O campo '{campo}' não pode estar vazio."
                }), 400
            
        campos = []
        valores = []

        for campo in campos_permitidos:
            if campo in dados:
                campos.append(f"{campo} = ?")
                valores.append(dados[campo])

        #VERIFICA SE ALGUM CAMPO VÁLIDO FOI ENVIADO
        if not campos:
            return jsonify({
                "erro": "Nenhum campo válido foi enviado para edição."
            }), 400

        valores.append(id)

        #VAI ATUALIZAR A TABELA
        cursor.execute(f"""
            UPDATE medicamentos
            SET {", ".join(campos)}
            WHERE id =?
        """, valores)

        conexao.commit()

        return jsonify({
            "msg": "Medicamento atualizado com sucesso.",
            "medicamento_id": id,
            "campos_atualizados": dados
        }), 200

    except Exception as e:
        if conexao:
            conexao.rollback()

        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if conexao:
            conexao.close()

#EXCLUIR UM MEDICAMENTO
@medicamentos_bp.route("/medicamentos/<int:id>", methods=['DELETE'])
@jwt_required()
@admin_required()
def excluir_medicamento(id):
    conexao = None

    try:
        conexao = connect()
        cursor = conexao.cursor()

        #VERIFICAR SE O MEDICAMENTO EXISTE
        cursor.execute("""
            SELECT 
                id,
                nome, 
                paciente_id, 
                status
            FROM medicamentos
            WHERE id=?
        """, (id,))

        medicamento = cursor.fetchone()

        if not medicamento:
            return jsonify({
                "erro": "Medicamento não encontrado."
            }), 404

        #VERIFICA SE JA ESTA INATIVO
        if medicamento["status"] == "inativo":
            return jsonify({
                "erro": "Este medicamento já está inativo."
            }), 400
            
        #DESATIVA O MEDICAMENTO
        cursor.execute("""
            UPDATE medicamentos
            SET status = 'inativo'
            WHERE id = ?
        """, (id,))

        conexao.commit()

        return jsonify({
            "msg": "Medicamento desativado com sucesso.",

            "medicamento": {
                "id": medicamento["id"],
                "nome": medicamento["nome"],
                "paciente_id": medicamento["paciente_id"],
                "status": "inativo"
            }
        }), 200

    except Exception as e:
        if conexao:
            conexao.rollback()

        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if conexao:
            conexao.close()
    