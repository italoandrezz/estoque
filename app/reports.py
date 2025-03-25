import io
import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from openpyxl import Workbook

def generate_excel(produtos):
    """Gera relatório em formato Excel"""
    output = io.BytesIO()
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Relatório de Estoque"

    # Cabeçalhos
    headers = ["Código", "Nome", "Quantidade", "Preço Unitário", "Valor Total"]
    sheet.append(headers)

    # Dados
    for produto in produtos:
        total = produto.quantidade * produto.preco
        sheet.append([
            produto.codigo,
            produto.nome,
            produto.quantidade,
            f"R$ {produto.preco:.2f}",
            f"R$ {total:.2f}"
        ])

    workbook.save(output)
    output.seek(0)
    return output

def generate_pdf(produtos):
    """Gera relatório em formato PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=cm,
        leftMargin=cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Obter estilos padrão e modificar apenas o necessário
    styles = getSampleStyleSheet()
    
    # Modificar o estilo Title existente em vez de adicionar um novo
    styles['Title'].fontName = 'Helvetica-Bold'
    styles['Title'].fontSize = 18
    styles['Title'].leading = 22
    styles['Title'].alignment = TA_CENTER
    styles['Title'].spaceAfter = 20
    
    elements = []
    elements.append(Paragraph("RELATÓRIO DE ESTOQUE", styles['Title']))
    elements.append(Paragraph(
        f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
        styles['Normal']
    ))
    elements.append(Spacer(1, 0.5*cm))
    
    data = [["Código", "Nome", "Quantidade", "Preço Unitário", "Valor Total"]]
    
    for produto in produtos:
        total = produto.quantidade * produto.preco
        data.append([
            produto.codigo,
            produto.nome,
            str(produto.quantidade),
            f"R$ {produto.preco:.2f}",
            f"R$ {total:.2f}"
        ])
    
    table = Table(data, colWidths=[2*cm, 6*cm, 2.5*cm, 3.5*cm, 3.5*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#3a7bd5')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
    ]))
    
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer

def generate_excel_historico(movimentacoes):
    """Gera histórico em formato Excel"""
    output = io.BytesIO()
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Histórico de Movimentações"

    headers = ["Data", "Produto", "Código", "Tipo", "Quantidade", "Usuário", "Motivo"]
    sheet.append(headers)

    for mov in movimentacoes:
        sheet.append([
            mov.data.strftime('%d/%m/%Y %H:%M'),
            mov.produto.nome,
            mov.produto.codigo,
            mov.tipo.upper(),
            mov.quantidade,
            mov.usuario.nome,
            mov.motivo or '-'
        ])

    workbook.save(output)
    output.seek(0)
    return output

def generate_pdf_historico(movimentacoes):
    """Gera histórico em formato PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=cm,
        leftMargin=cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    
    # Modificar o estilo Title existente
    styles['Title'].fontName = 'Helvetica-Bold'
    styles['Title'].fontSize = 18
    styles['Title'].leading = 22
    styles['Title'].alignment = TA_CENTER
    styles['Title'].spaceAfter = 20
    
    elements = []
    elements.append(Paragraph("HISTÓRICO DE MOVIMENTAÇÕES", styles['Title']))
    elements.append(Paragraph(
        f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
        styles['Normal']
    ))
    elements.append(Spacer(1, 0.5*cm))
    
    data = [["Data", "Produto", "Código", "Tipo", "Quantidade", "Usuário", "Motivo"]]
    
    for mov in movimentacoes:
        data.append([
            mov.data.strftime('%d/%m/%Y %H:%M'),
            mov.produto.nome,
            mov.produto.codigo,
            mov.tipo.upper(),
            str(mov.quantidade),
            mov.usuario.nome,
            mov.motivo or '-'
        ])
    
    table = Table(data, colWidths=[3*cm, 4*cm, 2*cm, 2*cm, 2*cm, 3*cm, 4*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#3a7bd5')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('FONTSIZE', (0,1), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
    ]))
    
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer