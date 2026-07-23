from flask import Flask
from routes.usuarios  import usuario_bp

app = Flask(__name__)

app.register_blueprint(usuario_bp)

app.run(host="localhost", port=5000, debug=True)