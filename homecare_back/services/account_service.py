from database.connect import connect
from werkzeug.security import generate_password_hash
from utils.response import validate_required_fields

from utils.queries import (
    create_account,
    create_patient,
    create_caregiver
)

def process_account_creation(new_user, allowed_roles):
    received_role = str(new_user.get("role", "")).strip().lower()

    required_fields = [
        "name",
        "email",
        "password",
        "confirm_password",
        "role"
    ]

    if received_role in ["patient", "caregiver"]:
        required_fields += [
            "cpf",
            "birth_date",
            "phone",
            "address"
        ]

    error = validate_required_fields(new_user, required_fields)

    if error:
        return None, error, 400

    if new_user["password"] != new_user["confirm_password"]:
        return None, "As senhas não coincidem.", 400

    if received_role not in allowed_roles:
        return None, "Função inválida.", 400

    connection = None

    try:
        connection = connect()
        cursor = connection.cursor()

        password_hash = generate_password_hash(
            new_user["password"]
        )

        user_id = create_account(
            cursor,
            new_user["name"],
            new_user["email"].strip().lower(),
            password_hash,
            received_role,
            new_user.get("cpf"),
            new_user.get("birth_date"),
            new_user.get("phone"),
            new_user.get("address")
        )

        if received_role == "patient":
            create_patient(cursor, user_id)

        elif received_role == "caregiver":
            create_caregiver(cursor, user_id)

        connection.commit()

        return user_id, None, 201

    except Exception as e:
        if connection:
            connection.rollback()

        return None, str(e), 500

    finally:
        if connection:
            connection.close()
