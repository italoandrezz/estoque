from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_
from . import db, login_manager
from .models import Produto, Usuario

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

def init_routes(app):
    @app.route('/')
    @login_required
    def index():
        pesquisa = request.args.get('pesquisa', '').strip()  # Termo de pesquisa
        pagina = request.args.get('pagina', 1, type=int)  # Página atual
        por_pagina = 10  # Número de produtos por página

        # Consulta base
        query = Produto.query

        # Aplicar filtro de pesquisa (nome ou código)
        if pesquisa:
            query = query.filter(or_(
                Produto.nome.ilike(f'%{pesquisa}%'),  # Pesquisa por nome (case-insensitive)
                Produto.codigo.ilike(f'%{pesquisa}%')  # Pesquisa por código (case-insensitive)
            ))

        # Paginação
        produtos = query.paginate(page=pagina, per_page=por_pagina)

        return render_template('index.html', produtos=produtos, pesquisa=pesquisa)

    @app.route('/adicionar', methods=['GET', 'POST'])
    @login_required
    def adicionar_produto():
        if request.method == 'POST':
            codigo = request.form['codigo']
            nome = request.form['nome']
            quantidade = int(request.form['quantidade'])
            preco = float(request.form['preco'])

            if Produto.query.filter_by(codigo=codigo).first():
                flash('Código já cadastrado!', 'danger')
                return redirect(url_for('adicionar_produto'))

            if quantidade < 0 or preco < 0:
                flash('Quantidade e preço devem ser valores positivos!', 'danger')
                return redirect(url_for('adicionar_produto'))

            produto = Produto(codigo=codigo, nome=nome, quantidade=quantidade, preco=preco)
            db.session.add(produto)
            db.session.commit()
            flash('Produto adicionado com sucesso!', 'success')
            return redirect(url_for('index'))

        return render_template('adicionar_produto.html')

    @app.route('/editar/<int:id>', methods=['GET', 'POST'])
    @login_required
    def editar_produto(id):
        produto = Produto.query.get_or_404(id)

        if request.method == 'POST':
            codigo = request.form['codigo']
            nome = request.form['nome']
            quantidade = int(request.form['quantidade'])
            preco = float(request.form['preco'])

            outro_produto = Produto.query.filter_by(codigo=codigo).first()
            if outro_produto and outro_produto.id != produto.id:
                flash('Código já cadastrado!', 'danger')
                return redirect(url_for('editar_produto', id=produto.id))

            if quantidade < 0 or preco < 0:
                flash('Quantidade e preço devem ser valores positivos!', 'danger')
                return redirect(url_for('editar_produto', id=produto.id))

            produto.codigo = codigo
            produto.nome = nome
            produto.quantidade = quantidade
            produto.preco = preco

            db.session.commit()
            flash('Produto atualizado com sucesso!', 'success')
            return redirect(url_for('index'))

        return render_template('editar_produto.html', produto=produto)

    @app.route('/excluir/<int:id>', methods=['POST'])
    @login_required
    def excluir_produto(id):
        produto = Produto.query.get_or_404(id)
        db.session.delete(produto)
        db.session.commit()
        flash('Produto excluído com sucesso!', 'success')
        return redirect(url_for('index'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form['email']
            senha = request.form['senha']
            usuario = Usuario.query.filter_by(email=email).first()

            if usuario and usuario.verificar_senha(senha):
                login_user(usuario)
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('index'))
            else:
                flash('E-mail ou senha incorretos.', 'danger')

        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Logout realizado com sucesso!', 'success')
        return redirect(url_for('login'))

    @app.route('/registro', methods=['GET', 'POST'])
    def registro():
        if request.method == 'POST':
            nome = request.form['nome']
            email = request.form['email']
            senha = request.form['senha']

            if Usuario.query.filter_by(email=email).first():
                flash('E-mail já cadastrado!', 'danger')
                return redirect(url_for('registro'))

            novo_usuario = Usuario(nome=nome, email=email)
            novo_usuario.set_senha(senha)
            db.session.add(novo_usuario)
            db.session.commit()
            flash('Registro realizado com sucesso! Faça login.', 'success')
            return redirect(url_for('login'))

        return render_template('registro.html')