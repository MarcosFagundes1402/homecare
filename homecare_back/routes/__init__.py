from routes.usuarios import usuario_bp
from routes.login import auth_bp
from routes.pacientes import pacientes_bp
from routes.cuidadores import cuidadores_bp
from homecare_back.routes.caregiver_patient import cuidadores_pacientes_bp
from routes.medicamentos import medicamentos_bp
from homecare_back.routes.administration_medications import administracao_medicamentos_bp
from routes.relatorios_diarios import relatorios_diarios_bp


def registrar_rotas(app):
    app.register_blueprint(usuario_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(pacientes_bp)
    app.register_blueprint(cuidadores_bp)
    app.register_blueprint(cuidadores_pacientes_bp)
    app.register_blueprint(medicamentos_bp)
    app.register_blueprint(administracao_medicamentos_bp)
    app.register_blueprint(relatorios_diarios_bp)