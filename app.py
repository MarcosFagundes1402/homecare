from flask import Flask
from routes.usuarios  import usuario_bp
from routes.auth import auth_bp
from flask_jwt_extended import JWTManager

app = Flask(__name__)

app.register_blueprint(auth_bp)
app.register_blueprint(usuario_bp)
app.config["JWT_SECRET_KEY"] = "chave_secreta"

jwt = JWTManager(app)

app.run(host="localhost", port=5000, debug=True)