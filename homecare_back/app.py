from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from routes import registrar_rotas

app = Flask(__name__)

CORS(app)

app.config["JWT_SECRET_KEY"] = "chave_secreta"

jwt = JWTManager(app)

registrar_rotas(app)

app.run(host="localhost", port=5000, debug=True)