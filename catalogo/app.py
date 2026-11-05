import json

import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request

app = Flask(__name__)


def coletar_produtos():
    produtos = []

    for numero in range(1, 101):
        link = f"https://scrapingsandbox.com/product/{numero}"
        resposta = requests.get(link, timeout=30)
        resposta.raise_for_status()
        html = BeautifulSoup(resposta.text, "html.parser")

        # O site apresenta os dados do produto dentro de uma tag <pre>.
        bloco = html.find("pre")
        if bloco is None:
            raise ValueError("Os dados do produto não foram encontrados.")

        dados = json.loads(bloco.get_text())
        produto = {
            "nome": dados["title"],
            "preco": dados.get("price"),
            "categoria": dados["category"],
            "avaliacao": dados.get("rating"),
            "link": link
        }
        produtos.append(produto)

    return produtos


def analisar_produtos(produtos):
    menor = None
    maior = None
    melhor = None
    soma = 0
    quantidade_com_preco = 0

    for produto in produtos:
        preco = produto["preco"]
        avaliacao = produto["avaliacao"]

        if preco is not None:
            soma += preco
            quantidade_com_preco += 1

            if menor is None or preco < menor["preco"]:
                menor = produto
            if maior is None or preco > maior["preco"]:
                maior = produto

        if avaliacao is not None:
            if melhor is None or avaliacao > melhor["avaliacao"]:
                melhor = produto

    media = None
    if quantidade_com_preco > 0:
        media = soma / quantidade_com_preco

    return {
        "quantidade": len(produtos),
        "menor": menor,
        "maior": maior,
        "media": media,
        "melhor": melhor
    }


# Permite escrever {{ produto.preco | dinheiro }} no HTML.
@app.template_filter("dinheiro")
def dinheiro(valor):
    if valor is None:
        return "Não disponível"
    return f"$ {valor:.2f}"


@app.route("/")
def inicio():
    categoria = request.args.get("categoria", "")
    categorias = []
    produtos_filtrados = []
    analise = None
    erro = None

    try:
        produtos = coletar_produtos()

        for produto in produtos:
            if produto["categoria"] not in categorias:
                categorias.append(produto["categoria"])
        categorias.sort()

        if categoria:
            if categoria not in categorias:
                erro = "Escolha uma categoria da lista."
            else:
                # O filtro é feito aqui no Python, depois da coleta.
                for produto in produtos:
                    if produto["categoria"] == categoria:
                        produtos_filtrados.append(produto)

                analise = analisar_produtos(produtos_filtrados)

    except (requests.RequestException, ValueError, KeyError, TypeError):
        erro = "Não foi possível coletar os produtos. Confira a conexão e tente novamente."

    return render_template(
        "index.html",
        categorias=categorias,
        categoria=categoria,
        produtos=produtos_filtrados,
        analise=analise,
        erro=erro
    )


if __name__ == "__main__":
    app.run(debug=False)
