from routes.users import user_bp
from routes.login import auth_bp
from routes.patients import patient_bp
from routes.caregiver import caregiver_bp
from routes.caregiver_patient import caregiver_patient_bp
from routes.medication import medicines_bp
from routes.administration_medications import administration_medications_bp
from routes.daily_reports import daily_reports_bp


def register_routes(app):
    app.register_blueprint(user_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(caregiver_bp)
    app.register_blueprint(caregiver_patient_bp)
    app.register_blueprint(medicines_bp)
    app.register_blueprint(administration_medications_bp)
    app.register_blueprint(daily_reports_bp)