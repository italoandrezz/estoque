from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_
from . import db, login_manager
from .models import Produto, Usuario, Movimentacao
from datetime import datetime
import random
import string

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

def gerar_codigo_unico():
    while True:
        # Gera um código de 4 dígitos aleatórios
        codigo = ''.join(random.choices(string.digits, k=4))
        # Verifica se o código já existe no banco de dados
        if not Produto.query.filter_by(codigo=codigo).first():
            return codigo

def init_routes(app):
    @app.route('/')
    @login_required
    def index():
        pesquisa = request.args.get('pesquisa', '').strip()
        pagina = request.args.get('pagina', 1, type=int)
        por_pagina = 10

        query = Produto.query

        if pesquisa:
            query = query.filter(or_(
                Produto.nome.ilike(f'%{pesquisa}%'),
                Produto.codigo.ilike(f'%{pesquisa}%')
            ))

        produtos = query.paginate(page=pagina, per_page=por_pagina)

        return render_template('index.html', produtos=produtos, pesquisa=pesquisa)

    @app.route('/adicionar', methods=['GET', 'POST'])
    @login_required
    def adicionar_produto():
        if request.method == 'POST':
            codigo = gerar_codigo_unico()  # Gera o código automaticamente
            nome = request.form.get('nome')
            quantidade = request.form.get('quantidade')
            preco = request.form.get('preco')

            # Validações
            if not nome or not quantidade or not preco:
                flash('Todos os campos são obrigatórios!', 'danger')
                return redirect(url_for('adicionar_produto'))

            try:
                quantidade = int(quantidade)
                preco = float(preco)
            except ValueError:
                flash('Quantidade e preço devem ser números válidos!', 'danger')
                return redirect(url_for('adicionar_produto'))

            if quantidade < 0 or preco < 0:
                flash('Quantidade e preço devem ser valores positivos!', 'danger')
                return redirect(url_for('adicionar_produto'))

            # Cria o produto com limite mínimo padrão (0)
            produto = Produto(codigo=codigo, nome=nome, quantidade=quantidade, preco=preco, limite_minimo=0)
            db.session.add(produto)
            db.session.commit()
            flash('Produto adicionado com sucesso!', 'success')
            return redirect(url_for('index'))

        # Se o método for GET, renderiza o template
        return render_template('adicionar_produto.html')

    @app.route('/editar/<int:id>', methods=['GET', 'POST'])
    @login_required
    def editar_produto(id):
        produto = Produto.query.get_or_404(id)

        if request.method == 'POST':
            codigo = produto.codigo  # Mantém o código original
            nome = request.form['nome']
            preco = float(request.form['preco'])

            if preco < 0:
                flash('O preço deve ser um valor positivo!', 'danger')
                return redirect(url_for('editar_produto', id=produto.id))

            produto.nome = nome
            produto.preco = preco
            # O limite mínimo não é alterado e permanece como 0

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

    @app.route('/entrada_produto/<int:id>', methods=['GET', 'POST'])
    @login_required
    def entrada_produto(id):
        produto = Produto.query.get_or_404(id)

        if request.method == 'POST':
            quantidade = int(request.form['quantidade'])
            motivo = request.form.get('motivo', '')

            if quantidade <= 0:
                flash('A quantidade deve ser maior que zero!', 'danger')
                return redirect(url_for('entrada_produto', id=produto.id))

            produto.quantidade += quantidade
            movimentacao = Movimentacao(
                produto_id=produto.id,
                usuario_id=current_user.id,
                tipo='entrada',
                quantidade=quantidade,
                motivo=motivo
            )
            db.session.add(movimentacao)
            db.session.commit()
            flash('Entrada de produto registrada com sucesso!', 'success')
            return redirect(url_for('index'))

        return render_template('entrada_produto.html', produto=produto)

    @app.route('/saida_produto/<int:id>', methods=['GET', 'POST'])
    @login_required
    def saida_produto(id):
        produto = Produto.query.get_or_404(id)

        if request.method == 'POST':
            quantidade = int(request.form['quantidade'])
            motivo = request.form.get('motivo', '')

            if quantidade <= 0:
                flash('A quantidade deve ser maior que zero!', 'danger')
                return redirect(url_for('saida_produto', id=produto.id))

            if produto.quantidade < quantidade:
                flash('Quantidade insuficiente em estoque!', 'danger')
                return redirect(url_for('saida_produto', id=produto.id))

            produto.quantidade -= quantidade
            movimentacao = Movimentacao(
                produto_id=produto.id,
                usuario_id=current_user.id,
                tipo='saida',
                quantidade=quantidade,
                motivo=motivo
            )
            db.session.add(movimentacao)
            db.session.commit()
            flash('Saída de produto registrada com sucesso!', 'success')
            return redirect(url_for('index'))

        return render_template('saida_produto.html', produto=produto)

    @app.route('/ajuste_estoque/<int:id>', methods=['GET', 'POST'])
    @login_required
    def ajuste_estoque(id):
        produto = Produto.query.get_or_404(id)

        if request.method == 'POST':
            nova_quantidade = int(request.form['quantidade'])
            motivo = request.form.get('motivo', '')

            if nova_quantidade < 0:
                flash('A quantidade não pode ser negativa!', 'danger')
                return redirect(url_for('ajuste_estoque', id=produto.id))

            diferenca = nova_quantidade - produto.quantidade
            tipo = 'entrada' if diferenca > 0 else 'saida'

            produto.quantidade = nova_quantidade
            movimentacao = Movimentacao(
                produto_id=produto.id,
                usuario_id=current_user.id,
                tipo=tipo,
                quantidade=abs(diferenca),
                motivo=motivo
            )
            db.session.add(movimentacao)
            db.session.commit()
            flash('Estoque ajustado com sucesso!', 'success')
            return redirect(url_for('index'))

        return render_template('ajuste_estoque.html', produto=produto)

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