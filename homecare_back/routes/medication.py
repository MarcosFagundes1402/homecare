from flask import Blueprint, jsonify, request
from database.connect import connect
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils import (
    roles_required,
    buscar_role,
    erro_role,
    paciente_status,
    vinculo_cp,
    validate_required_fields,
    validate_non_empty_field
)

medicines_bp = Blueprint("medicamentos",__name__)

#CRIA MEDICAMENTO PARA UM PACIENTE
@medicines_bp.route("/medicamentos/criar", methods=['POST'])
@jwt_required()
@roles_required("admin")
def create_medicine():
    connection = None

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "erro": "Dados não encontrados."
            }), 400

        required_fields = [
                    "paciente_id",
                    "nome",
                    "dosagem",
                    "horario"
                ]

        error = validate_required_fields(data, required_fields)

        if error:
            return jsonify({
                "erro": error
            }), 400
 

        connection = connect()
        cursor = connection.cursor()

        #VERIFICA SE É PACIENTE
        patient, error, role_name = buscar_role(cursor, data["paciente_id"], "paciente")

        if error:
            return erro_role(error, role_name, patient)

        #VERIFICA STATUS DO PACIENTE
        registered_patient = paciente_status(cursor, data["paciente_id"])

        if not registered_patient:
            return jsonify({
                "erro": "Paciente não encontrado."
            }), 404

        if registered_patient["status"] != "ativo":
            return jsonify({
                "erro": "Não é possível cadastrar medicamento para paciente inativo."
            }), 400
        
        #VERIFICA SE O MEDICAMENTO JÁ ESTÁ CADASTRADO
        cursor.execute("""
            SELECT id, dosagem 
            FROM medicamentos
            WHERE paciente_id = ? 
            AND nome = ?
            AND horario = ?
            AND status = 'ativo'
        """, (
            data["paciente_id"],
            data["nome"],
            data["horario"]
        ))

        existing_medicine = cursor.fetchone()

        if existing_medicine:
            return jsonify({
                "erro": "Já existe medicamento cadastrado neste horário.",
                "medicamento_id": existing_medicine["id"],
                "dosagem_atual": existing_medicine["dosagem"],
                "sugestao": "Edite o medicamento existente caso queira alterar a dosagem."
            }), 409
        
        #CRIA O MEDICAMENTO
        status = data.get("status", "ativo")

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
            data["paciente_id"],
            data["nome"],
            data["dosagem"],
            data["horario"],
            data.get("obs"),
            status
        ))

        medicine_id = cursor.lastrowid

        connection.commit()

        return jsonify({
            "msg": "Medicamento criado com sucesso.",

            "paciente": {
                "id": patient["id"],
                "nome": patient["nome"]
            },

            "medicamento":{
                "id": medicine_id,
                "nome": data["nome"],
                "dosagem": data["dosagem"],
                "horario": data["horario"],
                "obs": data.get("obs"),
                "status": status
            }
        }), 201

    except Exception as e:
        if connection:
            connection.rollback()

        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if connection:
            connection.close()

#ADMIN CONSULTA TODOS OS MEDICAMENTOS
@medicines_bp.route("/medicamentos/consultar", methods=['GET'])
@jwt_required()
@roles_required("admin")
def list_medicines():
    connection = None

    try:
        connection = connect()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                paciente_id,
                nome,
                dosagem,
                horario,
                obs,
                status
            FROM medicamentos
            ORDER BY nome
        """)

        medicines = cursor.fetchall()

        if not medicines:
            return jsonify({
                "medicamentos": []
            }), 200

        medicine_list = [dict(medicine) for medicine in medicines]

        return jsonify({
            "medicamentos": medicine_list
        }), 200

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500
    finally:
        if connection:
            connection.close()
        
# ADMIN CONSULTAR MEDICAMENTOS DE UM PACIENTE
@medicines_bp.route("/medicamentos/consultar-paciente/<int:id>", methods=['GET'])
@jwt_required()
@roles_required("admin", "cuidador")
def list_patient_medicines(patient_id):
    connection = None

    try:
        connection = connect()
        cursor = connection.cursor()

        logged_user_id = int(get_jwt_identity())

        cursor.execute("""
            SELECT role
            FROM usuarios
            WHERE id = ? 
        """, (logged_user_id,))

        logged_user = cursor.fetchone()

        if not logged_user:
            return jsonify({
                "msg": "Usuário não encontrado."
            }), 400

        logged_role = logged_user["role"]

        # VERIFICA SE O USUÁRIO É PACIENTE
        patient, error, role_name = buscar_role(cursor, patient_id, "paciente")

        if error:
            return erro_role(error, role_name, patient)

        # SE FOR CUIDADOR, PRECISA TER VINCULO COM O PACIENTE
        if logged_role == "cuidador":
            vinculo = vinculo_cp(cursor, logged_user_id, patient_id)

            if not vinculo:
                 return jsonify ({
                     "erro": "Você não possui vinculo com este paciente."
                 }), 403
            
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
        """, (patient_id,))

        medicines = cursor.fetchall()

        if not medicines:
            return jsonify({
                "paciente": {
                    "id": patient["id"],
                    "nome": patient["nome"]
                },
                "medicamentos": []
            }), 200

        medicine_list = [dict(medicine) for medicine in medicines]

        return jsonify({
            "paciente": {
                "id": patient["id"],
                "nome": patient["nome"]
            },
            "medicamentos": medicine_list
        }), 200

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if connection:
            connection.close()


#PACIENTE CONSULTA OS PROPRIOS MEDICAMENTOS
@medicines_bp.route("/medicamentos/meus-medicamentos", methods=['GET'])
@jwt_required()
@roles_required("paciente")
def my_medicines():
    connection = None

    try:
        patient_id = int(get_jwt_identity())

        connection = connect()
        cursor = connection.cursor()

        #BUSCA PACIENTE LOGADO
        patient, error, role_name = buscar_role(cursor, patient_id, "paciente")

        # RETORNA O ERRO SE A ROLE NAO EXISTIR
        if error:
            return erro_role(error, role_name, patient)

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
        """, (patient_id,))

        medicines = cursor.fetchall()

        if not medicines:
            return jsonify({
                "paciente": {
                    "id": patient["id"],
                    "nome": patient["nome"]
                },
                "medicamentos": []
            }), 200

        medicine_list = [dict(medicine) for medicine in medicines]

        return jsonify({
            "paciente":{
                "id": patient["id"],
                "nome": patient["nome"]
            },
            "medicamentos": medicine_list
        }), 200

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500

    finally:
        if connection:
            connection.close()

#CUIDADOR VERIFICA OS MEDICAMENTOS DO SEUS PACIENTES
@medicines_bp.route("/medicamentos/meus-pacientes", methods=['GET'])
@jwt_required()
@roles_required("cuidador")
def my_patients_medicines():
    connection = None

    try:
        caregiver_id = int(get_jwt_identity())

        connection = connect()
        cursor = connection.cursor()


        # VERIFICA SE O ID INFORMADO COMO CUIDADOR EXISTE
        caregiver, error, role_name = buscar_role(cursor, caregiver_id, "cuidador")

        # RETORNA O ERRO SE A ROLE NAO EXISTIR
        if error:
            return erro_role(error, role_name, caregiver)

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
        """, (caregiver_id,))        

        medicines = cursor.fetchall()

        if not medicines:
            return jsonify({
                "cuidador": {
                    "id": caregiver["id"],
                    "nome": caregiver["nome"]
                },
                "medicamentos": []
            }), 200

        medicine_list = []

        for medicine in medicines:
            medicine_list.append({
                "id": medicine["id"],
                "nome": medicine["nome"],
                "dosagem": medicine["dosagem"],
                "horario": medicine["horario"],
                "obs": medicine["obs"],
                "status": medicine["status"],

                "paciente": {
                    "id": medicine["paciente_id"],
                    "nome": medicine["paciente_nome"]
                }
            })

        return jsonify({
            "cuidador": {
                "id": caregiver["id"],
                "nome": caregiver["nome"]
            },

            "medicamentos": medicine_list
        }), 200

    except Exception as e:

        return jsonify({
            "erro": str(e)
        }), 500
    
    finally:
        if connection:
            connection.close()
        
#EDITA UM MEDICAMENTO
@medicines_bp.route("/medicamentos/<int:id>", methods=['PATCH'])
@jwt_required()
@roles_required("admin")
def edit_medicine(medicine_id):
    connection = None

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "erro": "Dados não encontrados."
            }), 400

        connection = connect()
        cursor = connection.cursor()

        #VERIFICA SE O MEDICAMENTO EXISTE
        cursor.execute("""
            SELECT id, paciente_id, nome
            FROM medicamentos
            WHERE id =?
        """,(medicine_id,))

        medicine = cursor.fetchone()

        if not medicine:
            return jsonify({
                "erro": "Medicamento não encontrado."
            }), 404

        #CAMPOS QUE PODE SER EDITADOS
        allowed_fields = [
            "nome",
            "dosagem",
            "horario",
            "obs",
            "status"
        ]

        #VERIFICA SE FOI ENVIADO CAMPO NAO PERMITIDO
        for field in data:
            if field not in allowed_fields:
                return jsonify({
                    "erro": f"O campo '{field}' não pode ser editado."
                }), 400

        #CAMPOS NAO PODEM FICAR VAZIOS
        non_empty_fields = [
            "nome",
            "dosagem",
            "horario",
            "status"
        ]

        error = validate_non_empty_field(data, non_empty_fields)

        if error:
            return jsonify({
                "erro": error
            }), 400
            
        fields = []
        values = []

        for field in allowed_fields:
            if field in data:
                fields.append(f"{field} = ?")
                values.append(data[field])

        #VERIFICA SE ALGUM CAMPO VÁLIDO FOI ENVIADO
        if not fields:
            return jsonify({
                "erro": "Nenhum campo válido foi enviado para edição."
            }), 400

        values.append(medicine_id)

        #VAI ATUALIZAR A TABELA
        cursor.execute(f"""
            UPDATE medicamentos
            SET {", ".join(fields)}
            WHERE id =?
        """, values)

        connection.commit()

        return jsonify({
            "msg": "Medicamento atualizado com sucesso.",
            "medicamento_id": medicine_id,
            "campos_atualizados": data
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

#EXCLUIR UM MEDICAMENTO
@medicines_bp.route("/medicamentos/desativar/<int:id>", methods=['DELETE'])
@jwt_required()
@roles_required("admin")
def disable_medicine(medicine_id):
    connection = None

    try:
        connection = connect()
        cursor = connection.cursor()

        #VERIFICAR SE O MEDICAMENTO EXISTE
        cursor.execute("""
            SELECT 
                id,
                nome, 
                paciente_id, 
                status
            FROM medicamentos
            WHERE id = ?
        """, (medicine_id,))

        medicine = cursor.fetchone()

        if not medicine:
            return jsonify({
                "erro": "Medicamento não encontrado."
            }), 404

        #VERIFICA SE JA ESTA INATIVO
        if medicine["status"] == "inativo":
            return jsonify({
                "erro": "Este medicamento já está inativo."
            }), 400
            
        #DESATIVA O MEDICAMENTO
        cursor.execute("""
            UPDATE medicamentos
            SET status = 'inativo'
            WHERE id = ?
        """, (medicine_id,))

        connection.commit()

        return jsonify({
            "msg": "Medicamento desativado com sucesso.",

            "medicamento": {
                "id": medicine["id"],
                "nome": medicine["nome"],
                "paciente_id": medicine["paciente_id"],
                "status": "inativo"
            }
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
    