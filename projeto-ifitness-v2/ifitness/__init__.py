import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "IFITNESS_SECRET_KEY",
    "troque-esta-chave-em-producao"
)
app.config["PERMANENT_SESSION_LIFETIME"] = 3600
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ifitness.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.path.join(
    app.root_path, "static", "uploads"
)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

from ifitness import modelos, rotas

with app.app_context():
    db.create_all()
