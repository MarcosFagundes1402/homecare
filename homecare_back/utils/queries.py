# BUSCA UM USUÁRIO PELO ID
def get_user_by_id(cursor, user_id):
    cursor.execute("""
        SELECT id, name, role, active
        FROM users
        WHERE id = %s
    """, (user_id,))

    return cursor.fetchone()

# BUSCA O VÍNCULO ENTRE UM CUIDADOR E UM PACIENTE
def get_caregiver_patient_link(cursor, caregiver_id, patient_id):
    cursor.execute("""
        SELECT id, active
        FROM caregiver_patient_links
        WHERE caregiver_id = %s
        AND patient_id = %s
    """,(
        caregiver_id,
        patient_id
    ))

    return cursor.fetchone()

# VALIDA SE O USUÁRIO EXISTE E POSSUI A ROLE ESPERADA
def validate_user_role(cursor, user_id, expected_role):
    user = get_user_by_id(cursor, user_id)

    role_name = expected_role.capitalize()

    if not user:
        return None, "nao_encontrado", role_name

    if user["role"].lower() != expected_role.lower():
        return user, "role_invalida", role_name

    return user, None, role_name

# BUSCA UM USUÁRIO PELO E-MAIL
def get_user_by_email(cursor, email):
    cursor.execute("""
            SELECT
                id,
                name,
                email,
                password_hash,
                role,
                active
            FROM users
            WHERE email = %s
    """, (email,))

    return cursor.fetchone()

# BUSCA TODOS OS USUÁRIOS
def get_all_users(cursor):
    cursor.execute("""
        SELECT
            id,
            name,
            email,
            role,
            active
        FROM users
        ORDER BY id
    """)

    return cursor.fetchall()

# BUSCA OUTRO USUÁRIO COM O MESMO E-MAIL, IGNORANDO O PRÓPRIO ID
def get_user_by_email_except_id(cursor, email, user_id):
    cursor.execute("""
        SELECT id
        FROM users
        WHERE email = %s
        AND id != %s
    """, (
        email,
        user_id
    ))

    return cursor.fetchone()

# CRIA UMA NOVA CONTA E RETORNA O ID DO USUÁRIO
def create_account(cursor, name, email, password_hash, role, cpf, birth_date, phone, address):
    cursor.execute("""
        INSERT INTO users (
            name,
            email,
            password_hash,
            role,
            cpf,
            birth_date,
            phone,
            address
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        name,
        email,
        password_hash,
        role,
        cpf,
        birth_date,
        phone,
        address
    ))

    return cursor.fetchone()["id"]

# CRIA O PERFIL DE PACIENTE PARA UM USUÁRIO
def create_patient(cursor, user_id):
    cursor.execute("""
        INSERT INTO patients (user_id)
        VALUES (%s)
    """, (user_id,))

# CRIA O PERFIL DE CUIDADOR PARA UM USUÁRIO
def create_caregiver(cursor, user_id):
    cursor.execute("""
        INSERT INTO caregivers (user_id)
        VALUES (%s)
    """, (user_id,))

# BUSCA O HASH DA SENHA DE UM USUÁRIO PELO ID
def get_user_password_by_id(cursor, user_id):
    cursor.execute("""
        SELECT id, password_hash
        FROM users
        WHERE id = %s
    """, (user_id,))

    return cursor.fetchone()

# ATUALIZA A SENHA DE UM USUÁRIO
def update_user_password(cursor, user_id, password_hash):
    cursor.execute("""
        UPDATE users
        SET password_hash = %s
        WHERE id = %s
    """, (
        password_hash,
        user_id
    ))

# BUSCA TODOS OS USUÁRIOS COM ROLE DE PACIENTE
def get_patient_data(cursor):
    cursor.execute("""
        SELECT
            id,
            name,
            cpf,
            birth_date,
            phone,
            address,
            active
        FROM users
        WHERE role = 'patient'
        ORDER BY id
    """)

    return cursor.fetchall()

# BUSCA OS DADOS DE UM PACIENTE PELO ID
def get_patient_data_by_id(cursor, user_id):
    cursor.execute("""
            SELECT
                id,
                name,
                cpf,
                birth_date,
                phone,
                address,
                active
            FROM users
            WHERE role = 'patient'
            AND id = %s
        """, (user_id,))

    return cursor.fetchone()

# BUSCA TODOS OS USUÁRIOS COM ROLE DE CUIDADOR
def get_caregiver_data(cursor):
    cursor.execute("""
            SELECT
                id,
                name,
                cpf,
                birth_date,
                phone,
                address,
                active
            FROM users
            WHERE role = 'caregiver'
        """)

    return cursor.fetchall()

# BUSCA OS DADOS DE UM CUIDADOR PELO ID
def get_caregiver_data_by_id(cursor, user_id):
    cursor.execute("""
            SELECT
                id,
                name,
                cpf,
                birth_date,
                phone,
                address,
                active
            FROM users
            WHERE role = 'caregiver'
            AND id = %s
        """, (user_id,))

    return cursor.fetchone()

# BUSCA OUTRO USUÁRIO COM O MESMO CPF, IGNORANDO O PRÓPRIO ID
def get_user_cpf_except_id(cursor, cpf, user_id):
    cursor.execute("""
                SELECT id
                FROM users
                WHERE cpf = %s
                AND id != %s
            """, (
                cpf,
                user_id
            ))

    return cursor.fetchone()

# ATUALIZA DINAMICAMENTE OS CAMPOS DE UM USUÁRIO
def update_user_fields(cursor, user_id, fields, values):

    params = values + [user_id]

    cursor.execute(f"""
            UPDATE users
            SET {", ".join(fields)}
            WHERE id = %s
        """, params)

# DESATIVA UM USUÁRIO
def disable_user(cursor, user_id):
    cursor.execute("""
        UPDATE users
        SET active = false
        WHERE id = %s
    """, (user_id,))

# CRIA UM VÍNCULO ENTRE CUIDADOR E PACIENTE
def generate_link(cursor, caregiver_id, patient_id):
    cursor.execute("""
        INSERT INTO caregiver_patient_links(
                caregiver_id,
                patient_id,
                created_date,
                created_time
            )
        VALUES (%s, %s, CURRENT_DATE, CURRENT_TIME)
         RETURNING id
    """, (
        caregiver_id,
        patient_id
    ))

    return cursor.fetchone()["id"]

# DESATIVA O VÍNCULO ENTRE CUIDADOR E PACIENTE
def disable_link(cursor, caregiver_id, patient_id):
    cursor.execute("""
        UPDATE caregiver_patient_links
        SET active = false
        WHERE caregiver_id = %s
        AND patient_id = %s
    """,(
        caregiver_id,
        patient_id
    ))

# BUSCA OS PACIENTES ATIVOS VINCULADOS A UM CUIDADOR
def get_patients_by_caregiver(cursor, caregiver_id):
    cursor.execute("""
        SELECT
            u.id,
            u.name,
            u.cpf,
            u.birth_date,
            u.phone,
            u.address,
            u.active
        FROM caregiver_patient_links cpl
        JOIN users u
            ON cpl.patient_id = u.id
        WHERE cpl.caregiver_id = %s
        AND cpl.active = true
    """, (caregiver_id,))

    return cursor.fetchall()

# BUSCA OS CUIDADORES ATIVOS VINCULADOS A UM PACIENTE
def get_caregivers_by_patient(cursor, patient_id):
    cursor.execute("""
        SELECT
            u.id,
            u.name,
            u.cpf,
            u.birth_date,
            u.phone,
            u.address,
            u.active
        FROM caregiver_patient_links cpl
        JOIN users u
            ON cpl.caregiver_id = u.id
        WHERE cpl.patient_id = %s
        AND cpl.active = true
    """, (patient_id,))

    return cursor.fetchall()

# CRIA UM NOVO PERÍODO NO HISTÓRICO DE UM VÍNCULO
def create_link_history(cursor, link_id):
    cursor.execute("""
        INSERT INTO caregiver_patient_link_history(
            link_id,
            started_date,
            started_time
            )
        VALUES (%s, CURRENT_DATE, CURRENT_TIME)
         RETURNING id
    """, (link_id,))

    return cursor.fetchone()["id"]

# FINALIZA O PERÍODO ATIVO NO HISTÓRICO DE UM VÍNCULO
def close_link_history(cursor, link_id):
    cursor.execute("""
        UPDATE caregiver_patient_link_history
        SET
            ended_date = CURRENT_DATE,
            ended_time = CURRENT_TIME
        WHERE link_id = %s
        AND ended_date IS NULL
        AND ended_time IS NULL
    """, (link_id,))

# VERIDICA SE O MEDICAMENTO JA ESTÁ CADASTRADO
def get_active_medicine(cursor, patient_id, name, schedule_time):
    cursor.execute("""
        SELECT
            id,
            disage
        FORM medicienes
        WHERE patient_id = %s
        AND name = $s
        AND dosage = $s
        AND schedule_time = $s
    """, (
            patient_id,
            name,
            schedule_time
        ))

    return cursor.fetchone()

# CRIAR O MEDICAMENTO
def register_medicine(cursor, patient_id, name, dosage, schedule_time, notes):
    cursor.execute("""
        INSERT INTO medicines(
            patient_id,
            name,
            dosage,
            schedule_time,
            notes
        )
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """,(
        patient_id,
        name,
        dosage,
        schedule_time,
        notes
    ))

    return cursor.fetchone()["id"]

# BUSCA TODOS OS MEDICAMENTOS ATIVOS
def get_medicines_data(cursor):

    cursor.execute("""
        SELECT
            id,
            patient_id,
            name,
            dosage,
            schedule_time,
            notes,
        WHERE active = true
        FROM medicines
        ORDER BY name
    """)

    return cursor.fetchall()

# BUSCA MEDICAMENTO DE UM PACIENTE
def get_medicines_by_patient_id(cursor, patient_id):

    cursor.execute("""
        SELECT
            id,
            name,
            dosage,
            schedule_time,
            notes,
            active
        FROM medicines
        WHERE patient_id
        ORDER BY id DESC
    """, (patient_id,))

    return cursor.fetchall()

# BUSCA OS MEDICAMENTOS DOS PACIENTES VINCULADOS AO CUIDADOR
def get_medicines_by_caregiver(cursor, caregiver_id):

    cursor.execute("""
        SELECT
            m.id,
            m.name,
            m.dosage,
            m.schedule_time,
            m.notes,
            m.active,

            u.id AS patient_id,
            u.name AS patient_name

        FROM medicines m

        JOIN caregiver_patient_links cpl
            ON cpl.patient_id = m.patient_id

        JOIN users u
            ON u.id = m.patient_id

        WHERE cpl.caregiver_id = %s
        AND cpl.active = true

        ORDER BY u.name, m.id DESC
    """, (caregiver_id,))

    return cursor.fetchall()

# VERIFICA SE O MEDICAMENTO EXISTE
def validate_medicine(cursor, medicine_id):
    cursor.execute("""
        SELECT
            id,
            patient_id,
            name,
            active
        FROM medicines
        WHERE id = %s
    """, (medicine_id,))

    return cursor.fetchone()

# ATUALIZA A TABELA DE MEDICAMENTOS
def update_medicine(cursor, medicines_id, fields, values):
    params = values + [medicines_id]

    cursor.execute(f"""
        UPDATE medicines
        SET {", ".join(fields)}
        WHERE id = %s
    """, params)

# ATUALIZA MEDICAMENTO COM STATUS DE DESATIVADO
def set_medicine_inactive(cursor, medicine_id):
    cursor.execute("""
        UPDATE medicines
        SET active = false
        WHERE id = %s
    """, (medicine_id,))

# REGISTRA UM NOVO RELATORIO
def register_daily_report(
        cursor,
        link_id,
        created_by_user_id,
        food,
        hygiene,
        blood_pressure,
        glucose,
        temperature,
        observations
):
    cursor.execute("""
        INSERT INTO daily_reports (
            link_id,
            created_by_user_id,
            food,
            hygiene,
            blood_pressure,
            glucose,
            temperature,
            observations,
            report_date,
            report_time
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s,
            CURRENT_DATE,
            CURRENT_TIME
        )
        RETURNING id
    """, (
        link_id,
        created_by_user_id,
        food,
        hygiene,
        blood_pressure,
        glucose,
        temperature,
        observations
    ))

    return cursor.fetchone()["id"]

# BUSCA OS RELATÓRIOS DIÁRIOS DE UM PACIENTE
def fetch_daily_reports_by_patient(cursor, patient_id):
    cursor.execute("""
        SELECT
            dr.id,
            dr.food,
            dr.hygiene,
            dr.blood_pressure,
            dr.glucose,
            dr.temperature,
            dr.observations,
            dr.report_date,
            dr.report_time,

            u.id AS created_by_user_id,
            u.name AS created_by_user_name,
            u.role AS created_by_user_role

        FROM daily_reports dr

        JOIN caregiver_patient_links cpl
            ON cpl.id = dr.link_id

        JOIN users u
            ON u.id = dr.created_by_user_id

        WHERE cpl.patient_id = %s
        AND dr.active = true

        ORDER BY dr.id DESC
    """, (patient_id,))

    return cursor.fetchall()

# BUSCA TODOS OS RELATÓRIOS DE TODOS OS PACIENTES
def fetch_all_daily_reports(cursor):
    cursor.execute("""
        SELECT
            dr.id,
            dr.food,
            dr.hygiene,
            dr.blood_pressure,
            dr.glucose,
            dr.temperature,
            dr.observations,
            dr.report_date,
            dr.report_time,

            p.id AS patient_id,
            p.name AS patient_name,

            u.id AS created_by_user_id,
            u.name AS created_by_user_name,
            u.role AS created_by_user_role

        FROM daily_reports dr

        JOIN caregiver_patient_links cpl
            ON cpl.id = dr.link_id

        JOIN users p
            ON p.id = cpl.patient_id

        JOIN users u
            ON u.id = dr.created_by_user_id

        ORDER BY dr.id DESC
    """)

    return cursor.fetchall()

# ATUALIZA O RELATORIO
def update_daily_report(cursor, report_id, fields, values):
    params = values + [report_id]

    cursor.execute(f"""
        UPDATE daily_reports
        SET {", ".join(fields)}
        WHERE ID = %s
    """, params)

# BUSCA UM RELATÓRIO DIÁRIO PELO ID
def fetch_daily_report_by_id(cursor, report_id):
    cursor.execute("""
        SELECT
            dr.id,
            dr.link_id,
            dr.created_by_user_id,
            dr.food,
            dr.hygiene,
            dr.blood_pressure,
            dr.glucose,
            dr.temperature,
            dr.observations,
            dr.report_date,
            dr.report_time,
            dr.active,

            cpl.patient_id

        FROM daily_reports dr

        JOIN caregiver_patient_links cpl
            ON cpl.id = dr.link_id

        WHERE dr.id = %s
    """, (report_id,))

    return cursor.fetchone()

# DESATIVA O RELATORIO
def set_daily_report_inactive(cursor, report_id):
    cursor.execute("""
        UPDATE daile_reports
        SET active = false
        WHERE id = %s
    """, (report_id,))

# VERIFICA SE EXISTE UMA ADMINISTRACAO NO MESMO HORARIO
def get_existing_administration(cursor, medicine_id, link_id):
    cursor.execute("""
        SELECT id
        FROM medicine_administrations
        WHERE medicine_id = %s
        AND link_id = %s
        AND administration_date = CURRENT_DATE
        AND EXTRACT(HOUR FROM administration_time) =
            EXCTRACT(HOUR FROM CURRENT_TIME)
        AND EXTRACT(MINUTE FROM administration_time) =
            EXCTRACT(MINUTE FROM CURRENT_TIME)
        AND active = true
    """,(
        medicine_id,
        link_id
    ))

    return cursor.fetchone()

# REGISTRAR ADMINISTRACAO
def create_medicine_administration(
        cursor,
        medicine_id,
        link_id,
        created_by_user_id,
        dosage_given,
        schedule_time,
        notes
):
    cursor.execute("""
        INSERT INTO medicine_administrations
            medicine_id,
            link_id,
            created_by_user_id,
            dosage_given,
            schedule_time,
            notes,
            administration_date,
            administration_time
        VALUES (%s, %s, %s, %s, %s, %s, CURRENT_DATE, CURRENT_TIME)
        RETURNING id
    """,(
        medicine_id,
        link_id,
        created_by_user_id,
        dosage_given,
        schedule_time,
        notes
    ))

    return cursor.fetchone()["id"]

# BUSCA TODAS AS ADMINISTRAÇÕES DE MEDICAMENTOS
def fetch_all_medicine_administrations(cursor):
    cursor.execute("""
        SELECT
            ma.id,
            ma.medicine_id,
            ma.link_id,
            ma.created_by_user_id,
            ma.dosage_given,
            ma.schedule_time,
            ma.notes,
            ma.administration_date,
            ma.administration_time,
            ma.active,

            m.name AS medicine_name,

            p.id AS patient_id,
            p.name AS patient_name,

            u.id AS created_by_user_id,
            u.name AS created_by_user_name,
            u.role AS created_by_user_role

        FROM medicine_administrations ma

        JOIN medicines m
            ON m.id = ma.medicine_id

        JOIN caregiver_patient_links cpl
            ON cpl.id = ma.link_id

        JOIN users p
            ON p.id = cpl.patient_id

        JOIN users u
            ON u.id = ma.created_by_user_id

        ORDER BY ma.id DESC
    """)

    return cursor.fetchall()

# BUSCA ADMINISTRACAO POR PACIENTE
def fetch_medicine_administrations_by_patient(cursor, patient_id):
    cursor.execute("""
        SELECT
            ma.id,
            ma.medicine_id,
            ma.link_id,
            ma.created_by_user_id,
            ma.dosage_given,
            ma.schedule_time,
            ma.notes,
            ma.administration_date,
            ma.administration_time,
            ma.active,

            m.name AS medicine_name,

            p.id AS patient_id,
            p.name AS patient_name,

            u.id AS created_by_user_id,
            u.name AS created_by_user_name,
            u.role AS created_by_user_role

        FROM medicine_administrations ma

        JOIN medicines m
            ON m.id = ma.medicine_id

        JOIN caregiver_patient_links cpl
            ON cpl.id = ma.link_id

        JOIN users p
            ON p.id = cpl.patient_id

        JOIN users u
            ON u.id = ma.created_by_user_id

        WHERE cpl.patient_id = %s

        ORDER BY ma.id DESC
    """, (patient_id,))

    return cursor.fetchall()

# BUSCAR ADMINISTRACAO POR CUIDADOR
def fetch_medicine_administrations_by_caregiver(cursor, caregiver_id):
    cursor.execute(
        """
        SELECT
            ma.id,
            ma.patient_id,
            ma.medicine_id,
            ma.schedule_time,
            ma.administration_time,
            ma.dosage_given,
            ma.notes,
            ma.active,

            p.name AS patient_name,

            m.name AS medicine_name,

            u.id AS created_by_user_id,
            u.name AS created_by_user_name,
            u.role AS created_by_user_role

        FROM medicine_administration ma

        JOIN caregivers_patient cp
            ON cp.patient_id = ma.patient_id

        JOIN users p
            ON p.id = ma.patient_id

        JOIN medicines m
            ON m.id = ma.medicine_id

        JOIN users u
            ON u.id = ma.created_by_user_id

        WHERE cp.caregiver_id = %s

        ORDER BY ma.id DESC
        """,
        (caregiver_id,),
    )

    return cursor.fetchall()

# BUSCA ADMINISTRACAO POR ID
def fetch_medicine_administration_by_id(cursor, administration_id):
    cursor.execute("""
        SELECT
            id,
            patient_id,
            medicine_id,
            created_by_user_id,
            schedule_time,
            dosage_given,
            notes,
            active
        FROM medicine_administrations
        WHERE id %s
    """,(administration_id,))

    return cursor.fetchone()

# ATUALIZA A ADMINISTRACOES
def update_medicine_administration(cursor, fields, values):
    cursor.execute(f"""
        UPDATE medicine_administration
        SET {", ".join(fields)}
        WHERE id = %s
    """, values)

def set_medicine_administration_inactive(cursor, administration_id):
    cursor.execute("""
        UPDATE medicine_administration
        SET active = FALSE
        WHERE id = %s
    """, (administration_id,))

# BUSCA ADMINISTRAÇÕES DE UM PACIENTE VINCULADO AO CUIDADOR
def fetch_medicine_administrations_by_caregiver_and_patient(
    cursor, caregiver_id, patient_id
):
    cursor.execute(
        """
        SELECT
            ma.id,
            ma.medicine_id,
            ma.link_id,
            ma.created_by_user_id,
            ma.dosage_given,
            ma.schedule_time,
            ma.notes,
            ma.administration_date,
            ma.administration_time,
            ma.active,

            m.name AS medicine_name,

            p.id AS patient_id,
            p.name AS patient_name,

            u.name AS created_by_user_name,
            u.role AS created_by_user_role

        FROM medicine_administrations ma

        JOIN medicines m
            ON m.id = ma.medicine_id

        JOIN caregiver_patient_links cpl
            ON cpl.id = ma.link_id

        JOIN users p
            ON p.id = cpl.patient_id

        JOIN users u
            ON u.id = ma.created_by_user_id

        WHERE cpl.caregiver_id = %s
          AND cpl.patient_id = %s

        ORDER BY ma.id DESC
    """,
        (caregiver_id, patient_id),
    )

    return cursor.fetchall()
