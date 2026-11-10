import os
from datetime import datetime
from functools import wraps
from ifitness.clima import buscar_clima

from flask import (
    render_template, request, redirect, url_for,
    session, flash, jsonify, abort
)
from werkzeug.utils import secure_filename
from sqlalchemy import func

from ifitness import app, db
from ifitness.modelos import Usuario, Atividade, Grupo


# Verifica se o usuário está conectado
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "usuario" not in session:
            flash(
                "Faça login para acessar esta página.",
                category="warning"
            )
            return redirect(url_for("login"))

        return f(*args, **kwargs)

    return decorated_function


# Busca uma atividade e confere se pertence ao usuário
def buscar_atividade_do_usuario(id):
    atividade = db.session.get(Atividade, id)

    if atividade is None:
        abort(404)

    if atividade.usuario_id != session.get("usuario_id"):
        abort(403)

    return atividade


# Páginas de erro
@app.errorhandler(403)
def acesso_negado(erro):
    return render_template(
        "erro.html",
        codigo=403,
        titulo="Acesso negado",
        mensagem="Você não tem permissão para acessar este recurso."
    ), 403


@app.errorhandler(404)
def nao_encontrado(erro):
    return render_template(
        "erro.html",
        codigo=404,
        titulo="Página não encontrada",
        mensagem="O endereço acessado não existe."
    ), 404


@app.errorhandler(500)
def erro_interno(erro):
    db.session.rollback()

    return render_template(
        "erro.html",
        codigo=500,
        titulo="Erro interno",
        mensagem="Ocorreu um erro inesperado. Tente novamente mais tarde."
    ), 500


# Página inicial
@app.route("/")
@login_required
def home():
    return render_template("dashboard.html")


# Lista as atividades do usuário conectado
@app.route("/atividades")
@login_required
def listar_atividades():
    atividades = (
        Atividade.query
        .filter_by(usuario_id=session["usuario_id"])
        .order_by(Atividade.data.desc())
        .all()
    )

    return render_template(
        "index.html",
        atividades=atividades
    )


# Tela de login
@app.route("/login")
def login():
    return render_template("login.html", resultado=None)


# Autenticação
@app.route("/autenticar", methods=["POST"])
def autenticar():
    email = request.form.get("email", "").strip().lower()
    senha = request.form.get("senha", "")

    usuario = Usuario.query.filter_by(email=email).first()

    if not usuario or not usuario.verificar_senha(senha):
        return render_template(
            "login.html",
            resultado="falha"
        ), 401

    session.permanent = True
    session["usuario_id"] = usuario.id
    session["usuario"] = usuario.email
    session["nome_usuario"] = usuario.nome

    resposta = redirect(url_for("home"))

    autorizou_cookies = (
        request.cookies.get("cookies_opcionais") == "sim"
    )

    if request.form.get("lembrar") and autorizou_cookies:
        resposta.set_cookie(
            "email_lembrado",
            email,
            max_age=30 * 24 * 60 * 60,
            httponly=False,
            samesite="Lax"
        )
    else:
        resposta.delete_cookie("email_lembrado")

    return resposta


# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# Escolha de cookies
@app.route("/escolher_cookies", methods=["POST"])
def escolher_cookies():
    escolha = (
        "sim"
        if request.form.get("escolha") == "sim"
        else "nao"
    )

    destino = (
        url_for("home")
        if session.get("usuario")
        else url_for("login")
    )

    resposta = redirect(destino)

    resposta.set_cookie(
        "cookies_opcionais",
        escolha,
        max_age=180 * 24 * 60 * 60,
        samesite="Lax"
    )

    if escolha == "nao":
        resposta.delete_cookie("email_lembrado")

    return resposta


# Cadastro de usuário
@app.route("/cadastro_usuario")
def cadastro_usuario():
    return render_template(
        "cadastro_usuario.html",
        resultado=None
    )


@app.route("/salvar_usuario", methods=["POST"])
def salvar_usuario():
    nome = request.form.get("nome", "").strip()
    email = request.form.get("email", "").strip().lower()
    senha = request.form.get("senha", "")
    nascimento = request.form.get("data_nascimento", "")
    genero = request.form.get("genero", "")

    if not all([nome, email, senha, nascimento, genero]):
        flash(
            "Preencha todos os campos obrigatórios.",
            "danger"
        )
        return render_template("cadastro_usuario.html")

    if Usuario.query.filter_by(email=email).first():
        return render_template(
            "cadastro_usuario.html",
            resultado="email_existe"
        )

    if len(senha) < 8 or len(senha) > 72:
        flash(
            "A senha deve ter de 8 a 72 caracteres.",
            "danger"
        )
        return render_template("cadastro_usuario.html")

 
    try:
        data_obj = datetime.strptime(
            nascimento, "%Y-%m-%d"
        ).date()
    except ValueError:
        flash("Data de nascimento inválida.", "danger")
        return render_template("cadastro_usuario.html")

    usuario = Usuario(
        nome=nome,
        email=email,
        data_nascimento=data_obj,
        genero=genero,
        foto=None
    )

    usuario.senha_criptografada = senha

    db.session.add(usuario)
    db.session.commit()

    flash("Usuário cadastrado com sucesso.", "success")

    return render_template(
        "login.html",
        resultado="cadastrado"
    )


# Perfil do usuário
@app.route("/perfil")
@login_required
def perfil():
    usuario = db.session.get(
        Usuario,
        session["usuario_id"]
    )

    return render_template(
        "perfil.html",
        usuario=usuario
    )


# Atualização do perfil
@app.route("/atualizar_perfil", methods=["POST"])
@login_required
def atualizar_perfil():
    usuario = db.session.get(
        Usuario,
        session["usuario_id"]
    )

    nome = request.form.get("nome", "").strip()
    nascimento = request.form.get("data_nascimento", "")
    genero = request.form.get("genero", "")

    if not all([nome, nascimento, genero]):
        flash("Preencha os campos obrigatórios.", "danger")
        return redirect(url_for("perfil"))

    try:
        data_obj = datetime.strptime(
            nascimento, "%Y-%m-%d"
        ).date()
    except ValueError:
        flash("Data de nascimento inválida.", "danger")
        return redirect(url_for("perfil"))

    usuario.nome = nome
    usuario.data_nascimento = data_obj
    usuario.genero = genero

    arquivo = request.files.get("foto")

    if arquivo and arquivo.filename:
        nome_seguro = secure_filename(arquivo.filename)

        os.makedirs(
            app.config["UPLOAD_FOLDER"],
            exist_ok=True
        )

        arquivo.save(
            os.path.join(
                app.config["UPLOAD_FOLDER"],
                nome_seguro
            )
        )

        usuario.foto = "/static/uploads/" + nome_seguro

    session["nome_usuario"] = usuario.nome

    db.session.commit()

    flash("Perfil atualizado com sucesso.", "success")

    return redirect(url_for("perfil"))


# Formulário de cadastro de atividade
@app.route("/cadastro_atividade", methods=["GET"])
@login_required
def cadastro_atividade():
    return render_template(
        "cadastro_atividade.html",
        id=0,
        atividade=None
    )


# Salvar ou editar atividade
@app.route("/salvar_atividade/<int:id>", methods=["POST"])
@login_required
def salvar_atividade(id):
    categoria = request.form.get("categoria")

    try:
        distancia = float(
            request.form.get("distancia", "")
        )

        duracao = int(
            request.form.get("duracao", "")
        )

        data = datetime.strptime(
            request.form.get("data", ""),
            "%Y-%m-%d"
        ).date()

    except (ValueError, TypeError):
        flash("Confira os dados da atividade.", "danger")
        return redirect(url_for("listar_atividades"))

    if not categoria or distancia < 0 or duracao < 0:
        flash("Confira os dados da atividade.", "danger")
        return redirect(url_for("listar_atividades"))

    if id != 0:
        atividade = buscar_atividade_do_usuario(id)

        atividade.categoria = categoria
        atividade.distancia = distancia
        atividade.duracao = duracao
        atividade.data = data

    else:
        atividade = Atividade(
            categoria=categoria,
            distancia=distancia,
            duracao=duracao,
            data=data,
            usuario_id=session["usuario_id"]
        )

        db.session.add(atividade)

    db.session.commit()

    flash("Atividade salva com sucesso.", "success")

    return redirect(url_for("listar_atividades"))


# Editar atividade
@app.route("/editar/<int:id>")
@login_required
def exibir_edicao(id):
    atividade = buscar_atividade_do_usuario(id)

    return render_template(
        "cadastro_atividade.html",
        atividade=atividade,
        id=id,
        resultado=None
    )


# Excluir atividade
@app.route("/excluir_atividade/<int:id>")
@login_required
def excluir_atividade(id):
    atividade = buscar_atividade_do_usuario(id)

    db.session.delete(atividade)
    db.session.commit()

    flash("Atividade excluída com sucesso.", "success")

    return redirect(url_for("listar_atividades"))


# Dados do painel
@app.route("/api/dados_dashboard")
@login_required
def api_dados_dashboard():
    uid = session["usuario_id"]

    total_distancia = (
        db.session.query(
            func.coalesce(func.sum(Atividade.distancia), 0)
        )
        .filter_by(usuario_id=uid)
        .scalar()
    )

    total_duracao = (
        db.session.query(
            func.coalesce(func.sum(Atividade.duracao), 0)
        )
        .filter_by(usuario_id=uid)
        .scalar()
    )

    total_treinos = (
        Atividade.query
        .filter_by(usuario_id=uid)
        .count()
    )

    categorias = (
        db.session.query(
            Atividade.categoria,
            func.count(Atividade.id)
        )
        .filter_by(usuario_id=uid)
        .group_by(Atividade.categoria)
        .all()
    )

    dias = (
        db.session.query(
            Atividade.data,
            func.sum(Atividade.distancia)
        )
        .filter_by(usuario_id=uid)
        .group_by(Atividade.data)
        .order_by(Atividade.data)
        .all()
    )

    return jsonify({
        "total_distancia": float(total_distancia),
        "total_duracao": int(total_duracao),
        "total_treinos": total_treinos,
        "por_categoria": {
            categoria: total
            for categoria, total in categorias
        },
        "por_dia": [
            {
                "data": data.isoformat(),
                "distancia": float(distancia)
            }
            for data, distancia in dias
        ]
    })


# Estatísticas
@app.route("/estatisticas")
@login_required
def estatisticas():
    return render_template("estatisticas.html")


# Quadro de líderes
@app.route("/quadro_lideres")
@login_required
def quadro_lideres():
    ranking = (
        db.session.query(
            Usuario,
            func.sum(Atividade.distancia).label("total_distancia"),
            func.count(Atividade.id).label("total_treinos"),
            func.sum(Atividade.duracao).label("total_tempo")
        )
        .join(Atividade, Usuario.id == Atividade.usuario_id)
        .group_by(Usuario.id)
        .order_by(func.sum(Atividade.distancia).desc())
        .all()
    )

    return render_template(
        "quadro_lideres.html",
        ranking=ranking
    )


# Conquistas
@app.route("/conquistas")
@login_required
def conquistas():
    resultados = (
        db.session.query(
            Atividade.categoria,
            func.count(Atividade.id).label("total")
        )
        .filter_by(usuario_id=session["usuario_id"])
        .group_by(Atividade.categoria)
        .all()
    )

    itens = []

    for categoria, total in resultados:
        if total < 5:
            nivel = "Iniciante"
            badge = "badge_initial"
            proximo = "Bronze"
            restantes = 5 - total
            progresso = total / 5 * 100

        elif total < 10:
            nivel = "Bronze"
            badge = "badge_bronze"
            proximo = "Prata"
            restantes = 10 - total
            progresso = (total - 5) / 5 * 100

        elif total < 15:
            nivel = "Prata"
            badge = "badge_silver"
            proximo = "Ouro"
            restantes = 15 - total
            progresso = (total - 10) / 5 * 100

        elif total < 20:
            nivel = "Ouro"
            badge = "badge_gold"
            proximo = "Platino"
            restantes = 20 - total
            progresso = (total - 15) / 5 * 100

        else:
            nivel = "Platino"
            badge = "badge_platinum"
            proximo = None
            restantes = 0
            progresso = 100

        itens.append({
            "categoria": categoria,
            "total": total,
            "nivel": nivel,
            "badge": badge,
            "proximo": proximo,
            "restantes": restantes,
            "progresso": int(progresso)
        })

    usuario = db.session.get(
        Usuario,
        session["usuario_id"]
    )

    return render_template(
        "conquistas.html",
        conquistas=itens,
        usuario=usuario
    )


# Alterar senha
@app.route("/alterar_senha", methods=["GET", "POST"])
@login_required
def alterar_senha():
    usuario = db.session.get(
        Usuario,
        session["usuario_id"]
    )

    if request.method == "POST":
        atual = request.form.get("senha_atual", "")
        nova = request.form.get("nova_senha", "")
        confirmar = request.form.get("confirmar_senha", "")

        if not usuario.verificar_senha(atual):
            flash("A senha atual está incorreta.", "danger")

        elif len(nova) < 8 or len(nova) > 72:
            flash(
                "A nova senha deve ter de 8 a 72 caracteres.",
                "danger"
            )

        elif nova != confirmar:
            flash(
                "A nova senha e a confirmação não são iguais.",
                "danger"
            )

        else:
            usuario.senha_criptografada = nova
            db.session.commit()

            flash("Senha alterada com sucesso.", "success")

            return redirect(url_for("perfil"))

    return render_template("alterar_senha.html")


# Painel de grupos
@app.route("/painel_grupos")
@login_required
def painel_grupos():
    return render_template("painel_grupos.html")


# Criar grupo
@app.route("/criar_grupo", methods=["GET", "POST"])
@login_required
def criar_grupo():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        descricao = request.form.get("descricao", "").strip()

        if nome and descricao:
            grupo = Grupo(
                nome=nome,
                descricao=descricao,
                criador_id=session["usuario_id"]
            )

            usuario = db.session.get(
                Usuario,
                session["usuario_id"]
            )

            grupo.membros.append(usuario)

            db.session.add(grupo)
            db.session.commit()

            flash("Grupo criado com sucesso.", "success")

            return redirect(url_for("meus_grupos"))

        flash("Preencha o nome e a descrição.", "danger")

    return render_template("criar_grupo.html")


# Meus grupos
@app.route("/meus_grupos")
@login_required
def meus_grupos():
    usuario = db.session.get(
        Usuario,
        session["usuario_id"]
    )

    return render_template(
        "meus_grupos.html",
        usuario=usuario
    )


# Associar-se a um grupo
@app.route("/associar_grupo", methods=["GET", "POST"])
@login_required
def associar_grupo():
    usuario = db.session.get(
        Usuario,
        session["usuario_id"]
    )

    if request.method == "POST":
        grupo_id = request.form.get("grupo_id", type=int)
        grupo = db.session.get(Grupo, grupo_id)

        if grupo and usuario not in grupo.membros:
            grupo.membros.append(usuario)
            db.session.commit()

            flash("Você entrou no grupo.", "success")

        return redirect(url_for("meus_grupos"))

    return render_template(
        "associar_grupo.html",
        grupos_disponiveis=Grupo.query.all()
    )


# Membros de um grupo
@app.route("/grupo/<int:id>/membros")
@login_required
def membros_grupo(id):
    grupo = db.session.get(Grupo, id)

    if grupo is None:
        abort(404)

    usuario = db.session.get(
        Usuario,
        session["usuario_id"]
    )

    if usuario not in grupo.membros:
        abort(403)

    return render_template(
        "membros_grupo.html",
        grupo=grupo
    )
# rotas que consomem APIs externas

# O navegador chama esta rota, e o servidor Flask consulta a API de clima


@app.route("/api/clima")
@login_required
def api_clima():
    dados = buscar_clima()
    if dados is None:
        # 503: o serviço de que dependemos está indisponível no momento
        return jsonify(erro="Não foi possível consultar o clima agora."), 503
    return jsonify(dados)


@app.route("/exluir_conta", methods=["POST", "GET"])
@app.route("/excluir_conta", methods=["POST"])
@login_required
def excluir_conta():
    usuario = db.session.get(
        Usuario,
        session["usuario_id"]
    )

    if usuario is None:
        session.clear()
        return redirect(url_for("login"))

    senha = request.form.get("senha", "")

    if not usuario.verificar_senha(senha):
        flash(
            "A senha atual está incorreta.",
            "danger"
        )

    else:
        try:
            # Exclui as atividades do usuário
            Atividade.query.filter_by(
                usuario_id=usuario.id
            ).delete()

            # Exclui a conta
            db.session.delete(usuario)
            db.session.commit()

            # Encerra a sessão
            session.clear()

            flash(
                "Conta excluída com sucesso.",
                "success"
            )

            return redirect(url_for("login"))

        except Exception:
            db.session.rollback()

            flash(
                "Não foi possível excluir a conta.",
                "danger"
            )

    return redirect(url_for("perfil"))
