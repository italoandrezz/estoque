from datetime import datetime
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_
from . import db, login_manager
from .models import Produto, Usuario, Movimentacao
import random

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

    

def gerar_codigo_unico():
    """Gera um código de 4 dígitos único"""
    while True:
        codigo = str(random.randint(1000, 9999))
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
    
    @app.context_processor
    def inject_now():
        return {'now': datetime.now()}

    @app.route('/adicionar', methods=['GET', 'POST'])
    @login_required
    def adicionar_produto():
        if request.method == 'POST':
            codigo = gerar_codigo_unico()
            nome = request.form.get('nome')
            quantidade = request.form.get('quantidade')
            preco = request.form.get('preco')

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
                flash('Quantidade e preço devem ser positivos!', 'danger')
                return redirect(url_for('adicionar_produto'))

            produto = Produto(
                codigo=codigo,
                nome=nome,
                quantidade=quantidade,
                preco=preco,
                limite_minimo=0
            )

            movimentacao = Movimentacao(
                produto=produto,
                usuario_id=current_user.id,
                tipo='entrada',
                quantidade=quantidade,
                motivo='Cadastro inicial',
                quantidade_anterior=0,
                quantidade_posterior=quantidade
            )

            db.session.add(produto)
            db.session.add(movimentacao)
            db.session.commit()

            flash(f'Produto adicionado! Código: {codigo}', 'success')
            return redirect(url_for('index'))

        return render_template('adicionar_produto.html')

    @app.route('/historico')
    @login_required
    def historico():
        page = request.args.get('page', 1, type=int)
        tipo = request.args.get('tipo', '')
        data_inicio = request.args.get('data_inicio', '')
        data_fim = request.args.get('data_fim', '')

        query = Movimentacao.query.order_by(Movimentacao.data.desc())

        if tipo:
            query = query.filter_by(tipo=tipo)
        
        if data_inicio:
            try:
                data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
                query = query.filter(Movimentacao.data >= data_inicio)
            except ValueError:
                flash('Data inválida!', 'warning')
        
        if data_fim:
            try:
                data_fim = datetime.strptime(data_fim + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
                query = query.filter(Movimentacao.data <= data_fim)
            except ValueError:
                flash('Data inválida!', 'warning')

        movimentacoes = query.paginate(page=page, per_page=10)

        return render_template(
            'historico.html',
            movimentacoes=movimentacoes,
            filtros={
                'tipo': tipo,
                'data_inicio': data_inicio.strftime('%Y-%m-%d') if isinstance(data_inicio, datetime) else data_inicio,
                'data_fim': data_fim.strftime('%Y-%m-%d') if isinstance(data_fim, datetime) else data_fim
            }
        )

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

            movimentacao = Movimentacao(
                produto_id=produto.id,
                usuario_id=current_user.id,
                tipo='entrada',
                quantidade=quantidade,
                motivo=motivo,
                quantidade_anterior=produto.quantidade,
                quantidade_posterior=produto.quantidade + quantidade
            )
            db.session.add(movimentacao)
            
            produto.quantidade += quantidade
            db.session.commit()
            
            flash('Entrada de produto registrada!', 'success')
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

            movimentacao = Movimentacao(
                produto_id=produto.id,
                usuario_id=current_user.id,
                tipo='saida',
                quantidade=quantidade,
                motivo=motivo,
                quantidade_anterior=produto.quantidade,
                quantidade_posterior=produto.quantidade - quantidade
            )
            db.session.add(movimentacao)
            
            produto.quantidade -= quantidade
            db.session.commit()
            
            flash('Saída de produto registrada!', 'success')
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

            movimentacao = Movimentacao(
                produto_id=produto.id,
                usuario_id=current_user.id,
                tipo=tipo,
                quantidade=abs(diferenca),
                motivo=motivo,
                quantidade_anterior=produto.quantidade,
                quantidade_posterior=nova_quantidade
            )
            db.session.add(movimentacao)
            
            produto.quantidade = nova_quantidade
            db.session.commit()
            
            flash('Estoque ajustado com sucesso!', 'success')
            return redirect(url_for('index'))

        return render_template('ajuste_estoque.html', produto=produto)

    @app.route('/editar/<int:id>', methods=['GET', 'POST'])
    @login_required
    def editar_produto(id):
        produto = Produto.query.get_or_404(id)

        if request.method == 'POST':
            produto.nome = request.form['nome']
            produto.preco = float(request.form['preco'])
            db.session.commit()
            flash('Produto atualizado!', 'success')
            return redirect(url_for('index'))

        return render_template('editar_produto.html', produto=produto)

    @app.route('/excluir/<int:id>', methods=['POST'])
    @login_required
    def excluir_produto(id):
        produto = Produto.query.get_or_404(id)
        db.session.delete(produto)
        db.session.commit()
        flash('Produto excluído!', 'success')
        return redirect(url_for('index'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form['email']
            senha = request.form['senha']
            usuario = Usuario.query.filter_by(email=email).first()

            if usuario and usuario.verificar_senha(senha):
                login_user(usuario)
                flash('Login realizado!', 'success')
                return redirect(url_for('index'))
            else:
                flash('E-mail ou senha incorretos!', 'danger')

        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Logout realizado!', 'success')
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
            flash('Registro realizado! Faça login.', 'success')
            return redirect(url_for('login'))

        return render_template('registro.html')