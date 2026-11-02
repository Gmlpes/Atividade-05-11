
# ==========================================================
# IMPORTAÇÃO DAS BIBLIOTECAS
# ==========================================================

# Flask é o framework responsável por criar nossa aplicação Web.
# render_template permite enviar informações do Python para o HTML.
# request permite receber informações enviadas pelo formulário.
from flask import Flask, render_template, request

# Requests é utilizado para acessar o site e baixar seu HTML.
import requests

# BeautifulSoup interpreta o HTML recebido e permite localizar
# as informações dos produtos dentro da página.
from bs4 import BeautifulSoup


# ==========================================================
# CRIAÇÃO DA APLICAÇÃO
# ==========================================================

# Inicializa a aplicação Flask.
# É através dela que conseguimos conectar o Python com as páginas HTML.
app = Flask(__name__)


# ==========================================================
# CONFIGURAÇÕES
# ==========================================================

# Endereço do site de onde serão coletados os produtos.
URL_SITE = "https://scrapingsandbox.com/data-table"

# Define quantas páginas serão percorridas durante a pesquisa.
# Utilizamos 10 páginas para coletar uma quantidade maior de produtos.
PAGINAS = 10

# Lista que armazena as categorias encontradas.
# Assim, não precisamos buscar as categorias novamente
# toda vez que o usuário acessar a página inicial.
categorias_salvas = []


# ==========================================================
# FUNÇÃO DE WEB SCRAPING
# ==========================================================

# Esta função é responsável por acessar o site e coletar os produtos.
# Ela recebe como parâmetro a quantidade de páginas que deverá percorrer.
def buscar_produtos(quantidade_paginas):

    # Lista que armazenará os produtos coletados.
    produtos = []

    # Armazena os links já encontrados para evitar produtos repetidos.
    links_vistos = []

    # Estrutura de repetição responsável pela paginação.
    # Começa na página 1 e continua até a quantidade informada.
    for pagina in range(1, quantidade_paginas + 1):

        # Monta o endereço de cada página automaticamente.
        # Exemplo: https://scrapingsandbox.com/data-table?page=2
        url = f"{URL_SITE}?page={pagina}"

        # Faz uma requisição HTTP para acessar a página.
        resposta = requests.get(url)

        # Verifica se o site respondeu corretamente.
        # Se houver erro, interrompe a coleta.
        if resposta.status_code != 200:
            break

        # Recebe o HTML da página e utiliza o BeautifulSoup
        # para interpretar sua estrutura.
        soup = BeautifulSoup(resposta.text, "html.parser")

        # Localiza todas as linhas da tabela de produtos.
        # A tag <tr> representa uma linha de uma tabela HTML.
        linhas = soup.find_all("tr")

        # Conta quantos produtos novos foram encontrados na página.
        novos = 0

        # Percorre cada linha da tabela.
        for linha in linhas:

            # Localiza as células de cada linha.
            # A tag <td> representa uma célula da tabela.
            celulas = linha.find_all("td")

            # Ignora linhas que não possuem pelo menos 7 células.
            # Isso evita tentar coletar informações de linhas incompletas
            # ou do cabeçalho da tabela.
            if len(celulas) < 7:
                continue

            # Extrai as informações das colunas da tabela.
            # get_text() recupera somente o texto, sem as tags HTML.
            # strip=True remove espaços desnecessários.
            nome = celulas[2].get_text(strip=True)
            categoria = celulas[4].get_text(strip=True)
            preco_texto = celulas[5].get_text(strip=True)
            nota_texto = celulas[6].get_text(strip=True)

            # Localiza o link dentro da célula que contém o nome.
            tag_link = celulas[2].find("a")

            # Monta o endereço completo do produto.
            link = "https://scrapingsandbox.com" + tag_link["href"]

            # Verifica se o produto já foi coletado.
            # Se o link já estiver na lista, ignora o produto.
            if link in links_vistos:
                continue

            # Armazena o novo link e atualiza a quantidade encontrada.
            links_vistos.append(link)
            novos = novos + 1

            # Converte o preço de texto para número decimal.
            # Exemplo: "$155.62" passa a ser 155.62.
            # Isso permite realizar cálculos matemáticos.
            preco = float(preco_texto.replace("$", "").replace(",", ""))

            # Converte a avaliação para número decimal.
            # Caso não exista uma avaliação válida, armazena None.
            try:
                nota = float(nota_texto)
            except ValueError:
                nota = None

            # Organiza as informações de cada produto em um dicionário.
            # Cada produto possui nome, preço, categoria, avaliação e link.
            registro = {
                "nome": nome,
                "preco": preco,
                "categoria": categoria,
                "avaliacao": nota,
                "link": link
            }

            # Adiciona o produto à lista principal.
            produtos.append(registro)

        # Se nenhuma informação nova foi encontrada,
        # interrompe a paginação para evitar percorrer páginas repetidas.
        if novos == 0:
            break

    # Retorna todos os produtos coletados para a parte principal do programa.
    return produtos


# ==========================================================
# PÁGINA INICIAL
# ==========================================================

# Define a rota principal da aplicação.
# Quando o usuário acessa o endereço inicial, esta função é executada.
@app.route("/")
def inicio():

    # Verifica se as categorias já foram carregadas.
    # Se a lista estiver vazia, realiza a coleta.
    if len(categorias_salvas) == 0:

        # Coleta produtos das primeiras 5 páginas
        # para identificar as categorias disponíveis.
        produtos = buscar_produtos(5)

        # Percorre os produtos coletados.
        for produto in produtos:

            # Adiciona somente categorias que ainda não existem na lista.
            if produto["categoria"] not in categorias_salvas:
                categorias_salvas.append(produto["categoria"])

        # Organiza as categorias em ordem alfabética.
        categorias_salvas.sort()

    # Abre o arquivo index.html e envia as categorias para ele.
    # O Jinja utiliza essas informações para preencher o formulário.
    return render_template("index.html", categorias=categorias_salvas)


# ==========================================================
# ROTA RESPONSÁVEL PELA PESQUISA
# ==========================================================

# Esta rota recebe os dados enviados pelo formulário HTML.
# O método POST é utilizado para enviar a categoria selecionada.
@app.route("/pesquisar", methods=["POST"])
def pesquisar():

    # Recupera a categoria escolhida pelo usuário no formulário.
    categoria_escolhida = request.form.get("categoria")

    # Executa o Web Scraping em 10 páginas do site.
    # Todos os produtos coletados são armazenados na variável todos.
    todos = buscar_produtos(PAGINAS)

    # ======================================================
    # FILTRAGEM DOS PRODUTOS
    # ======================================================

    # Cria uma lista vazia para armazenar somente os produtos
    # que pertencem à categoria escolhida pelo usuário.
    produtos_filtrados = []

    # Percorre todos os produtos coletados.
    for produto in todos:

        # Compara a categoria do produto com a categoria selecionada.
        if produto["categoria"] == categoria_escolhida:

            # Se forem iguais, adiciona o produto à lista filtrada.
            produtos_filtrados.append(produto)

    # ======================================================
    # ANÁLISE DOS PRODUTOS
    # ======================================================

    # Conta quantos produtos foram encontrados na categoria.
    quantidade = len(produtos_filtrados)

    # Inicializa as variáveis com None.
    # Isso evita erros caso nenhum produto seja encontrado.
    menor = None
    maior = None
    media = None
    melhor = None

    # Só realiza os cálculos se houver produtos na categoria.
    if quantidade > 0:

        # Considera o primeiro produto como referência inicial
        # para encontrar o menor e o maior preço.
        menor = produtos_filtrados[0]
        maior = produtos_filtrados[0]

        # Variável responsável por acumular os preços.
        soma = 0

        # Percorre todos os produtos da categoria selecionada.
        for produto in produtos_filtrados:

            # Verifica se o preço atual é menor que o menor encontrado.
            if produto["preco"] < menor["preco"]:
                menor = produto

            # Verifica se o preço atual é maior que o maior encontrado.
            if produto["preco"] > maior["preco"]:
                maior = produto

            # Soma o preço do produto ao valor acumulado.
            soma = soma + produto["preco"]

            # Verifica a avaliação do produto.
            # Produtos sem avaliação são ignorados.
            if produto["avaliacao"] is not None:

                # Se ainda não existe uma melhor avaliação
                # ou se a avaliação atual for maior, atualiza o resultado.
                if melhor is None or produto["avaliacao"] > melhor["avaliacao"]:
                    melhor = produto

        # Calcula a média dos preços.
        # Divide a soma de todos os preços pela quantidade de produtos.
        media = soma / quantidade

    # ======================================================
    # ENVIO DOS RESULTADOS PARA O HTML
    # ======================================================

    # render_template abre resultado.html e envia todas as informações.
    # O Jinja utiliza essas variáveis para apresentar os resultados
    # ao usuário no navegador.
    return render_template(
        "resultado.html",

        # Categoria pesquisada.
        categoria=categoria_escolhida,

        # Lista contendo somente os produtos da categoria escolhida.
        produtos=produtos_filtrados,

        # Quantidade de produtos encontrados.
        quantidade=quantidade,

        # Produto com menor preço.
        menor=menor,

        # Produto com maior preço.
        maior=maior,

        # Média dos preços.
        media=media,

        # Produto com melhor avaliação.
        melhor=melhor,

        # Quantidade total de produtos coletados antes da filtragem.
        total=len(todos),

        # Quantidade de páginas percorridas.
        paginas=PAGINAS
    )


# ==========================================================
# EXECUÇÃO DA APLICAÇÃO
# ==========================================================

# Verifica se este arquivo está sendo executado diretamente.
# Se estiver, inicia o servidor Flask.
if __name__ == "__main__":

    # debug=True permite identificar erros durante o desenvolvimento.
    app.run(debug=True)
