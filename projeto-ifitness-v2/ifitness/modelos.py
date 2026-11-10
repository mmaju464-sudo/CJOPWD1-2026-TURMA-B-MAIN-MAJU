from ifitness import db, bcrypt

membros_grupos = db.Table(
    "membros_grupos",
    db.Column(
        "usuario_id",
        db.Integer,
        db.ForeignKey("usuarios.id"),
        primary_key=True
    ),
    db.Column(
        "grupo_id",
        db.Integer,
        db.ForeignKey("grupos.id"),
        primary_key=True
    )
)


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    data_nascimento = db.Column(db.Date, nullable=False)
    genero = db.Column(db.String(20), nullable=False)
    foto = db.Column(db.String(200))

    atividades = db.relationship(
        "Atividade",
        backref="usuario",
        cascade="all, delete-orphan",
        lazy=True
    )

    grupos = db.relationship(
        "Grupo",
        secondary=membros_grupos,
        back_populates="membros"
    )

    @property
    def senha_criptografada(self):
        raise AttributeError("A senha não pode ser lida.")

    @senha_criptografada.setter
    def senha_criptografada(self, senha_texto):
        self.senha = bcrypt.generate_password_hash(
            senha_texto
        ).decode("utf-8")

    def verificar_senha(self, senha_texto):
        return bcrypt.check_password_hash(
            self.senha,
            senha_texto
        )


class Atividade(db.Model):
    __tablename__ = "atividades"

    id = db.Column(db.Integer, primary_key=True)
    categoria = db.Column(db.String(100), nullable=False)
    distancia = db.Column(db.Float, nullable=False)
    duracao = db.Column(db.Integer, nullable=False)
    data = db.Column(db.Date, nullable=False)

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False
    )


class Grupo(db.Model):
    __tablename__ = "grupos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=False)

    criador_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False
    )

    membros = db.relationship(
        "Usuario",
        secondary=membros_grupos,
        back_populates="grupos"
    )

    criador = db.relationship(
        "Usuario",
        foreign_keys=[criador_id]
    )
