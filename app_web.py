from flask import Flask, render_template, request
from datetime import datetime, timedelta
import sqlite3

app = Flask(__name__)

db_veiculos = 'database/veiculos.db'
db_clientes = 'database/clientes.db'
db_reservas = 'database/reservas.db'
db_formas_de_pagamento = 'database/formas de pagamento.db'

data_atual_datetime = datetime.now()
data_atual_str = datetime.strftime(data_atual_datetime, "%Y-%m-%d")


# função para obter os veículos da pesquisa do utilizador
def obter_parametros_pesquisa(plano, marca_veiculo=None, modelo_veiculo=None, categoria=None, tipo_transmissao=None,
                              capacidade_passageiros=None, preco_dia=None, tipo_veiculo=None, tipo_combustivel=None):
    with sqlite3.connect(db_veiculos) as conn:
        cursor = conn.cursor()
        query = 'SELECT * FROM veiculos WHERE plano=? AND disponibilidade=?'
        parametros = [plano, "Disponivel"]

        if marca_veiculo:
            query += 'AND marca=?'
            parametros.append(marca_veiculo)

        if modelo_veiculo:
            query += 'AND modelo=?'
            parametros.append(modelo_veiculo)

        if categoria:
            query += 'AND categoria=?'
            parametros.append(categoria)

        if tipo_transmissao:
            query += 'AND tipo_transmissao=?'
            parametros.append(tipo_transmissao)

        if capacidade_passageiros:
            capacidade_passageiros_input = capacidade_passageiros.split("-")
            capacidade_passageiros_min = int(capacidade_passageiros_input[0])
            capacidade_passageiros_max = int(capacidade_passageiros_input[1])

            query += 'AND capacidade_passageiros BETWEEN ? AND ?'
            parametros.extend((capacidade_passageiros_min, capacidade_passageiros_max))

        if preco_dia:
            precos_input = preco_dia.split("-")
            preco_min = int(precos_input[0])
            preco_max = int(precos_input[1])

            query += 'AND preco_dia BETWEEN ? AND ?'
            parametros.extend((preco_min, preco_max))

        if tipo_veiculo:
            query += 'AND tipo_veiculo=?'
            parametros.append(tipo_veiculo)

        if tipo_combustivel:
            query += 'AND tipo_combustivel=?'
            parametros.append(tipo_combustivel)

        cursor.execute(query, parametros)
        pesquisa_dados_veiculos = cursor.fetchall()
    return pesquisa_dados_veiculos


# função para obter as caracteristicas da página do utilizador em função do plano
def obter_caracteristicas_do_plano(plano):
    if plano == "gold":
        cor_h1 = "goldenrod"
        cor_card = "linear-gradient(40deg, rgba(255, 223, 0, 0.8), #ffd700)"
        veiculos_opcoes_pesquisa = obter_dados_veiculos_gold()

        return cor_h1, cor_card, veiculos_opcoes_pesquisa

    elif plano == "silver":
        cor_h1 = "gray"
        cor_card = "linear-gradient(40deg, #d0d0d0, #c0c0c0)"
        veiculos_opcoes_pesquisa = obter_dados_veiculos_silver()

        return cor_h1, cor_card, veiculos_opcoes_pesquisa

    elif plano == "economico":
        cor_h1 = "gray"
        cor_card = "#ffffff"
        veiculos_opcoes_pesquisa = obter_dados_veiculos_economico()

        return cor_h1, cor_card, veiculos_opcoes_pesquisa


# função para alterar a disponibilidade, data de revisão e legalização
def alterar_disponibilidade():
    with sqlite3.connect(db_reservas) as conn_reservas, sqlite3.connect(db_veiculos) as conn_veiculos:

        cursor_reservas = conn_reservas.cursor()
        cursor_veiculos = conn_veiculos.cursor()

        cursor_reservas.execute('SELECT data_levantamento, data_devolucao, id_veiculo FROM reservas')
        veiculos_reservados = cursor_reservas.fetchall()

        cursor_veiculos.execute('SELECT id, data_ultima_revisao, data_proxima_revisao, data_ultima_legalizacao, '
                                'data_proxima_legalizacao FROM veiculos')
        datas_veiculos_revisao_legalizacao = cursor_veiculos.fetchall()

        # função para alterar a disponibilidade do veículo caso este esteja reservado
        for reserva in veiculos_reservados:

            data_levantamento_datetime = datetime.strptime(reserva[0], "%Y-%m-%d %H:%M:%S")
            data_levantamento_str = datetime.strftime(data_levantamento_datetime, "%Y-%m-%d")

            data_devolucao_datetime = datetime.strptime(reserva[1], "%Y-%m-%d %H:%M:%S")
            data_devolucao_str = datetime.strftime(data_devolucao_datetime, "%Y-%m-%d")

            if data_levantamento_str <= data_atual_str <= data_devolucao_str:
                cursor_veiculos.execute('UPDATE veiculos SET disponibilidade = "Reservado" WHERE id = ?',
                                        (reserva[2],))

            if data_devolucao_str == data_atual_str:
                cursor_veiculos.execute('UPDATE veiculos SET disponibilidade = "Disponivel" WHERE id = ?',
                                        (reserva[2],))

        # função para alterar a data de revisão e legalização
        for datas in datas_veiculos_revisao_legalizacao:

            um_ano = timedelta(days=365)
            data_proxima_revisao_legalizacao_datetime = data_atual_datetime + um_ano
            data_proxima_revisao_legalizacao_str = datetime.strftime(data_proxima_revisao_legalizacao_datetime,
                                                                     "%Y-%m-%d")

            data_proxima_revisao = datas[2]
            data_proxima_legalizacao = datas[4]

            if data_proxima_revisao == data_atual_str:
                cursor_veiculos.execute(
                    'UPDATE veiculos SET data_ultima_revisao = ?, data_proxima_revisao= ? WHERE id = ?',
                    (data_atual_str, data_proxima_revisao_legalizacao_str, datas[0]))

            if data_proxima_legalizacao == data_atual_str:
                cursor_veiculos.execute(
                    'UPDATE veiculos SET data_ultima_legalizacao = ?, data_proxima_legalizacao= ? WHERE id = ?',
                    (data_atual_str, data_proxima_revisao_legalizacao_str, datas[0]))


# Função para converter as datas de reserva para o formato "%Y-%m-%d"
def obter_dados_reserva_formatados(usuario):
    dados_reservas_utilizador = obter_dados_reservas(usuario)
    dados_reservas_formatados = []

    for datas_reservas in dados_reservas_utilizador:
        data_levantamento = datetime.strptime(datas_reservas[4], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
        data_devolucao = datetime.strptime(datas_reservas[5], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
        dados_reservas_formatados.append(datas_reservas[:4] + (data_levantamento, data_devolucao) + datas_reservas[6:])
    return dados_reservas_formatados


# Função para determinar se uma reserva está em uso
def reserva_utilizada(data_levantamento):
    if data_atual_str < data_levantamento:
        return False
    else:
        return True


# Função para extrair dados dos veículos disponíveis do plano economico
def obter_dados_veiculos_economico():
    with sqlite3.connect(db_veiculos) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM veiculos WHERE plano=? AND disponibilidade=?', ("economico", "Disponivel"))
        dados_veiculos_economico = cursor.fetchall()
    return dados_veiculos_economico


# Função para extrair dados dos veículos disponíveis do plano silver
def obter_dados_veiculos_silver():
    with sqlite3.connect(db_veiculos) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM veiculos WHERE plano=? AND disponibilidade=?', ("silver", "Disponivel"))
        dados_veiculos_silver = cursor.fetchall()
    return dados_veiculos_silver


# Função para extrair dados dos veículos disponíveis do plano gold
def obter_dados_veiculos_gold():
    with sqlite3.connect(db_veiculos) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM veiculos WHERE plano=? AND disponibilidade=?', ("gold", "Disponivel"))
        dados_veiculos_gold = cursor.fetchall()
    return dados_veiculos_gold


# Função para extrair dados das reservas do usuario
def obter_dados_reservas(usuario):
    with sqlite3.connect(db_reservas) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM reservas WHERE usuario=? ORDER BY data_levantamento DESC', (usuario,))
        dados_reservas_utilizador = cursor.fetchall()
    return dados_reservas_utilizador


# Função para extrair dados do usuario
def obter_dados_utilizador(usuario):
    conn = sqlite3.connect(db_clientes)
    cursor = conn.cursor()
    cursor.execute('SELECT nome, apelido, idade, genero, plano, cidadania FROM clientes WHERE usuario = ?',
                   (usuario,))
    dados_utilizador = cursor.fetchone()
    conn.close()
    return dados_utilizador


# Função para determinar o plano associado ao usuário
def obter_plano_usuario(usuario):
    conn = sqlite3.connect(db_clientes)
    cursor = conn.cursor()
    cursor.execute('SELECT plano FROM clientes WHERE usuario = ?', (usuario,))
    dados_plano = cursor.fetchone()
    conn.close()
    return dados_plano


# Função para verificar se o utilizador está registado na base de dados
def verificar_existencia_do_utilizador(usuario, password, plano):
    with sqlite3.connect(db_clientes) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT usuario FROM clientes WHERE usuario = ? AND senha = ? AND plano = ?',
                       (usuario, password, plano))
        utilizador = cursor.fetchall()
    return utilizador


@app.route('/')
def home():
    return render_template('PaginaLogIn.html')


@app.route('/login', methods=['POST'])
def login():
    usuario = request.form.get('usuario')
    password = request.form.get('senha')

    dados_utilizador = obter_dados_utilizador(usuario)
    alterar_disponibilidade()

    cor_h1 = None
    cor_card = None
    dados_veiculos = None
    veiculos_opcoes_pesquisa = None

    resultado_gold = verificar_existencia_do_utilizador(usuario, password, "gold")
    resultado_silver = verificar_existencia_do_utilizador(usuario, password, "silver")
    resultado_economico = verificar_existencia_do_utilizador(usuario, password, "economico")

    if resultado_gold:
        cor_h1, cor_card, veiculos_opcoes_pesquisa = obter_caracteristicas_do_plano("gold")
        dados_veiculos = obter_dados_veiculos_gold()

    elif resultado_silver:
        cor_h1, cor_card, veiculos_opcoes_pesquisa = obter_caracteristicas_do_plano("silver")
        dados_veiculos = obter_dados_veiculos_silver()

    elif resultado_economico:
        cor_h1, cor_card, veiculos_opcoes_pesquisa = obter_caracteristicas_do_plano("economico")
        dados_veiculos = obter_dados_veiculos_economico()

    if not any([resultado_economico, resultado_silver, resultado_gold]):
        return render_template('PaginaLogIn.html', condicao=True)

    if not dados_veiculos:
        return render_template('PaginaCliente.html', dados_veiculos=dados_veiculos, dados_utilizador=dados_utilizador,
                               usuario=usuario, cor_card=cor_card, cor_h1=cor_h1, condicao1=True)
    else:
        return render_template('PaginaCliente.html', dados_veiculos=dados_veiculos,
                               veiculos_opcoes_pesquisa=veiculos_opcoes_pesquisa,
                               dados_utilizador=dados_utilizador, usuario=usuario, cor_card=cor_card, cor_h1=cor_h1)


@app.route('/selecionar-data', methods=['POST'])
def selecionar_data():
    usuario = request.form.get('usuario')
    plano_tuple = obter_plano_usuario(usuario)
    plano = plano_tuple[0]
    cor_h1 = obter_caracteristicas_do_plano(plano)

    return render_template('VerDisponibilidade.html', usuario=usuario, cor_h1=cor_h1[0])


@app.route('/ver-disponibilidade', methods=['POST'])
def ver_disponibilidade():
    preco = request.form.get('preco')
    data_levantamento_str = request.form.get('data_input_levantamento')
    data_devolucao_str = request.form.get('data_input_devolucao')
    usuario = request.form.get('usuario')
    id_veiculo = request.form.get('id do veiculo')

    plano_tuple = obter_plano_usuario(usuario)
    plano = plano_tuple[0]
    cor_h1 = obter_caracteristicas_do_plano(plano)

    # converter a string para um objeto datetime
    data_levantamento_datetime = datetime.strptime(data_levantamento_str, "%Y-%m-%d")
    data_devolucao_datetime = datetime.strptime(data_devolucao_str, "%Y-%m-%d")

    # Calcular dias de aluguer
    dias_aluguer = data_devolucao_datetime - data_levantamento_datetime

    # Obter datas de reserva do veiculo selecionado
    with sqlite3.connect(db_reservas) as con:
        cursor = con.cursor()
        cursor.execute('SELECT * FROM reservas WHERE id_veiculo=?', (id_veiculo,))
        dados_veiculo_selecionado = cursor.fetchall()
        con.commit()

    # adicionar datas do veiculo selecionado
    datas_disponibilidade_veiculo = []
    for data in dados_veiculo_selecionado:
        datas_disponibilidade_veiculo.append((data[4], data[5]))

    veiculo_disponivel = False
    if data_atual_str <= data_levantamento_str and data_levantamento_datetime < data_devolucao_datetime:
        veiculo_disponivel = True
        for reserva in datas_disponibilidade_veiculo:
            data_inicio_reserva_datetime = datetime.strptime(reserva[0], "%Y-%m-%d %H:%M:%S")
            data_fim_reserva_datetime = datetime.strptime(reserva[1], "%Y-%m-%d %H:%M:%S")

            if (data_levantamento_datetime == data_fim_reserva_datetime or data_devolucao_datetime == data_inicio_reserva_datetime) \
                    or (data_inicio_reserva_datetime < data_devolucao_datetime and data_fim_reserva_datetime > data_levantamento_datetime):
                veiculo_disponivel = False
                break

    if veiculo_disponivel:
        if plano == "gold":
            preco_do_plano = 600
            preco_do_seguro = 300

        elif plano == "silver":
            preco_do_plano = 250
            preco_do_seguro = 150

        else:
            preco_do_plano = 50
            preco_do_seguro = 75

        preco_dia = int(dias_aluguer.days) * float(preco)
        preco_total = preco_dia + preco_do_plano + preco_do_seguro

        return render_template('FinalizarCompra.html', preco_do_plano=preco_do_plano, preco_do_seguro=preco_do_seguro,
                               preco_total=preco_total, usuario=usuario, dias_aluguer=dias_aluguer, cor_h1=cor_h1[0])
    else:
        return render_template('VerDisponibilidade.html', condicao=True, usuario=usuario, cor_h1=cor_h1[0])


@app.route('/pagar', methods=['POST'])
def pagar():
    id_do_veiculo = request.form.get('id do veiculo')
    imagem_veiculo = request.form.get('imagem do veiculo')
    marca_do_veiculo = request.form.get('marca do veiculo')
    modelo_do_veiculo = request.form.get('modelo do veiculo')
    data_devolucao_str = request.form.get('data_input_devolucao')
    data_levantamento_str = request.form.get('data_input_levantamento')
    preco_total = request.form.get('preco_total')
    usuario = request.form.get('usuario')
    dias_aluguer_str = request.form.get('dias_aluguer')
    preco_dia = request.form.get('preco_dia')
    preco_seguro = request.form.get('preco_seguro')
    preco_plano = request.form.get('preco_do_plano')
    forma_pagamento = request.form.get('metodo_pagamento')

    # Obter o número de dias alugados
    dias_aluguer_split = dias_aluguer_str.split()
    dias_aluguer = int(dias_aluguer_split[0])

    # converter a string para um objeto datetime
    data_devolucao_datetime = datetime.strptime(data_devolucao_str, "%Y-%m-%d")
    data_levantamento_datetime = datetime.strptime(data_levantamento_str, "%Y-%m-%d")

    # Inserir dados na tabela forma_pagamento
    if forma_pagamento == "cartao credito":
        nome_cartao = request.form.get('nome_cartao')
        num_cartao = request.form.get('numero_cartao')
        validade_cartao = request.form.get('validade_cartao')
        cvv = request.form.get('cvv')

        if not num_cartao or not validade_cartao or not cvv:
            return render_template('FinalizarCompra.html', preco_plano=preco_plano, preco_seguro=preco_seguro,
                                   preco_total=preco_total, usuario=usuario, dias_aluguer=dias_aluguer, condicao=True)

        with sqlite3.connect(db_formas_de_pagamento) as con:
            cursor = con.cursor()
            query = 'INSERT INTO cartao_credito (nome_cartao, num_cartao, validade_cartao, cvv, preco_total, usuario) ' \
                    'VALUES (?, ?, ?, ?, ?, ?)'
            cursor.execute(query, (nome_cartao, num_cartao, validade_cartao, cvv, preco_total, usuario))
            con.commit()

    if forma_pagamento == "paypal":
        email_paypal = request.form.get('email_paypal')
        password_paypal = request.form.get('password_paypal')

        if not email_paypal or not password_paypal:
            return render_template('FinalizarCompra.html', preco_plano=preco_plano, preco_seguro=preco_seguro,
                                   preco_total=preco_total, usuario=usuario, dias_aluguer=dias_aluguer, condicao=True)

        with sqlite3.connect(db_formas_de_pagamento) as con:
            cursor = con.cursor()
            query = 'INSERT INTO paypal (email_paypal, password_paypal, preco_total, usuario) VALUES (?, ?, ?, ?)'
            cursor.execute(query, (email_paypal, password_paypal, preco_total, usuario))
            con.commit()

    if forma_pagamento == "mbway":
        num_telemovel = request.form.get('num_telemovel')

        if not num_telemovel:
            return render_template('FinalizarCompra.html', preco_plano=preco_plano, preco_seguro=preco_seguro,
                                   preco_total=preco_total, usuario=usuario, dias_aluguer=dias_aluguer, condicao=True)

        with sqlite3.connect(db_formas_de_pagamento) as con:
            cursor = con.cursor()
            query = 'INSERT INTO mbway (num_telemovel , preco_total, usuario) VALUES (?, ?, ?)'
            cursor.execute(query, (num_telemovel, preco_total, usuario))
            con.commit()

    # Inserir dados na tabela reserva
    with sqlite3.connect(db_reservas) as con:
        cursor = con.cursor()
        query = 'INSERT INTO reservas (marca_veiculo, modelo_veiculo, data_levantamento, data_devolucao, preco_dia, ' \
                'preco_seguro, preco_plano, preco_total, dias_aluguer, usuario, forma_pagamento, id_veiculo, imagem_veiculo) ' \
                'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
        cursor.execute(query, (
            marca_do_veiculo, modelo_do_veiculo, data_levantamento_datetime, data_devolucao_datetime, preco_dia,
            preco_seguro, preco_plano, preco_total, dias_aluguer, usuario, forma_pagamento,
            id_do_veiculo, imagem_veiculo))
        con.commit()

    return render_template('PagamentoConcluido.html', usuario=usuario)


@app.route('/pesquisar-veiculos', methods=['POST'])
def pesquisar_veiculos():
    usuario = request.form.get('usuario')
    marca_veiculo = request.form.get('marca_veiculo')
    modelo_veiculo = request.form.get('modelo_veiculo')
    categoria = request.form.get('categoria')
    tipo_transmissao = request.form.get('tipo_transmissao')
    capacidade_passageiros = request.form.get('capacidade_passageiros')
    preco_dia = request.form.get('preco_dia')
    tipo_veiculo = request.form.get('tipo_veiculo')
    tipo_combustivel = request.form.get('tipo_combustivel')

    # Obter dados plano e dados do utilizador
    plano_tuple = obter_plano_usuario(usuario)
    plano = plano_tuple[0]
    dados_utilizador = obter_dados_utilizador(usuario)

    # Obter dados dos veículos pesquisados
    dados_veiculos_pesquisados = obter_parametros_pesquisa(plano, marca_veiculo, modelo_veiculo, categoria,
                                                           tipo_transmissao, capacidade_passageiros, preco_dia,
                                                           tipo_veiculo, tipo_combustivel)

    # Obter caracteristicas da pagina do utilizador
    cor_h1, cor_card, veiculos_opcoes_pesquisa = obter_caracteristicas_do_plano(plano)

    if not dados_veiculos_pesquisados:
        return render_template('PaginaCliente.html', dados_veiculos=dados_veiculos_pesquisados,
                               veiculos_opcoes_pesquisa=veiculos_opcoes_pesquisa, dados_utilizador=dados_utilizador,
                               usuario=usuario, plano=plano, cor_card=cor_card, cor_h1=cor_h1, condicao=True)
    else:
        return render_template('PaginaCliente.html', dados_veiculos=dados_veiculos_pesquisados,
                               veiculos_opcoes_pesquisa=veiculos_opcoes_pesquisa, dados_utilizador=dados_utilizador,
                               usuario=usuario, plano=plano, cor_h1=cor_h1, cor_card=cor_card)


@app.route('/ver-frota', methods=['POST'])
def ver_frota():
    usuario = request.form.get('usuario')

    plano_tuple = obter_plano_usuario(usuario)
    plano = plano_tuple[0]
    dados_utilizador = obter_dados_utilizador(usuario)

    alterar_disponibilidade()

    # Obter caracteristicas do pagina do utilizador
    cor_h1, cor_card, veiculos_opcoes_pesquisa = obter_caracteristicas_do_plano(plano)

    return render_template('PaginaCliente.html', dados_veiculos=veiculos_opcoes_pesquisa,
                           veiculos_opcoes_pesquisa=veiculos_opcoes_pesquisa,
                           dados_utilizador=dados_utilizador, usuario=usuario, plano=plano, cor_h1=cor_h1,
                           cor_card=cor_card)


@app.route('/sobre', methods=['POST'])
def sobre():
    usuario = request.form.get('usuario')
    plano_tuple = obter_plano_usuario(usuario)
    plano = plano_tuple[0]

    cor_h1 = obter_caracteristicas_do_plano(plano)
    dados_utilizador = obter_dados_utilizador(usuario)

    return render_template('Sobre.html', dados_utilizador=dados_utilizador, usuario=usuario, plano=plano,
                           cor_h1=cor_h1[0])


@app.route('/area-cliente', methods=['POST'])
def area_cliente():
    usuario = request.form.get('usuario')
    plano_tuple = obter_plano_usuario(usuario)
    plano = plano_tuple[0]

    cor_h1 = obter_caracteristicas_do_plano(plano)
    dados_utilizador = obter_dados_utilizador(usuario)
    dados_reservas = obter_dados_reserva_formatados(usuario)
    quantidade_veiculos_alugados = len(dados_reservas)

    with sqlite3.connect(db_reservas) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT SUM(preco_total), SUM(dias_aluguer) FROM reservas WHERE usuario = ?', (usuario,))
        tupla_resultado = cursor.fetchall()

    preco_total = tupla_resultado[0][0]
    dias_aluguer = tupla_resultado[0][1]

    return render_template('AreaCliente.html', dados_utilizador=dados_utilizador, usuario=usuario,
                           dados_reservas=dados_reservas, plano=plano, preco_total=preco_total,
                           quantidade_veiculos_alugados=quantidade_veiculos_alugados, dias_aluguer=dias_aluguer,
                           cor_h1=cor_h1[0])


@app.route('/reservas', methods=['POST'])
def reservas():
    usuario = request.form.get('usuario')
    plano_tuple = obter_plano_usuario(usuario)
    plano = plano_tuple[0]
    dados_utilizador = obter_dados_utilizador(usuario)

    dados_reservas_utilizador = obter_dados_reserva_formatados(usuario)

    cor_h1, cor_card, veiculos_opcoes_pesquisa = obter_caracteristicas_do_plano(plano)

    return render_template('Reservas.html', dados_reservas_utilizador=dados_reservas_utilizador,
                           dados_utilizador=dados_utilizador, usuario=usuario, plano=plano, cor_h1=cor_h1,
                           cor_card=cor_card)


@app.route('/cancelar-reserva', methods=['POST'])
def cancelar_reserva():
    usuario = request.form.get('usuario')
    id_reserva = request.form.get('id da reserva')
    data_levantamento = request.form.get('data levantamento')

    plano_tuple = obter_plano_usuario(usuario)
    plano = plano_tuple[0]
    dados_utilizador = obter_dados_utilizador(usuario)

    reserva = reserva_utilizada(data_levantamento)

    if reserva:
        condicao = True
    else:
        condicao = False
        with sqlite3.connect(db_reservas) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM reservas WHERE id=?', (id_reserva,))

    cor_h1, cor_card, veiculos_opcoes_pesquisa = obter_caracteristicas_do_plano(plano)

    dados_reservas_utilizador = obter_dados_reserva_formatados(usuario)
    return render_template('Reservas.html', dados_reservas_utilizador=dados_reservas_utilizador,
                           dados_utilizador=dados_utilizador,
                           usuario=usuario, plano=plano, cor_h1=cor_h1, cor_card=cor_card, condicao=condicao)


@app.route('/alterar-reserva', methods=['POST'])
def alterar_reserva():
    usuario = request.form.get('usuario')
    id_reserva = request.form.get('id da reserva')
    data_levantamento = request.form.get('data levantamento')

    plano_tuple = obter_plano_usuario(usuario)
    plano = plano_tuple[0]
    dados_utilizador = obter_dados_utilizador(usuario)

    reserva = reserva_utilizada(data_levantamento)
    dados_reservas_utilizador = obter_dados_reserva_formatados(usuario)

    if reserva:
        # Obter caracteristicas do pagina do utilizador
        cor_h1, cor_card, veiculos_opcoes_pesquisa = obter_caracteristicas_do_plano(plano)
    else:
        with sqlite3.connect(db_reservas) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM reservas WHERE id=?', (id_reserva,))
        return render_template('VerDisponibilidade.html', usuario=usuario, plano=plano)

    return render_template('Reservas.html', dados_reservas_utilizador=dados_reservas_utilizador,
                           dados_utilizador=dados_utilizador,
                           usuario=usuario, plano=plano, cor_h1=cor_h1, cor_card=cor_card, condicao=True)


@app.route('/criar-conta')
def criar_conta():
    return render_template('CriarConta.html')


@app.route('/registar-cliente', methods=['POST'])
def registar_cliente():
    nome = request.form.get('nome')
    apelido = request.form.get('apelido')
    idade = request.form.get('idade')
    genero = request.form.get('genero')
    usuario = request.form.get('usuario')
    senha = request.form.get('senha')
    plano = request.form.get('plano')
    cidadania = request.form.get('cidadania')
    confirmar_senha = request.form.get('confirmar_senha')

    with sqlite3.connect(db_clientes) as con:
        cursor = con.cursor()
        cursor.execute('SELECT usuario FROM clientes WHERE usuario = ?', (usuario,))
        todos_usuarios = cursor.fetchall()

        # Verificar se o usuário já está registrado
        if todos_usuarios:
            return render_template('CriarConta.html', condicao1=True)

        if senha == confirmar_senha:
            with sqlite3.connect(db_clientes) as conn:
                cursor = conn.cursor()
                query = 'INSERT INTO clientes (nome, apelido, idade, genero, usuario, senha, ' \
                        'plano, cidadania) VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
                cursor.execute(query, (nome, apelido, idade, genero, usuario, senha, plano, cidadania))
                conn.commit()
                return render_template("ContaCriada.html")
        else:
            return render_template('CriarConta.html', condicao=True)


if __name__ == '__main__':
    app.run(debug=True)
