import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin
from time import sleep
from utils.logger import logger  # Logger configurado via Loguru

# python -m scripts.scraper


# URL base do site a ser raspado
BASE_URL = "https://books.toscrape.com/"


def get_soup(url):
    """
    Realiza uma requisição HTTP para a URL fornecida e retorna um objeto BeautifulSoup.
    Retorna None caso a página não exista (404) ou ocorra qualquer erro de conexão.
    """
    try:
        response = requests.get(url)

        if response.status_code == 404:
            logger.warning(f"Página não encontrada (404): {url}")
            return None

        response.raise_for_status()
        return BeautifulSoup(response.content, "html.parser")

    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao acessar {url}: {e}")
        return None


def parse_rating(rating_str):
    """
    Converte o nome da classificação (ex: 'Three') em número inteiro correspondente.
    """
    ratings_map = {
        "One": 1,
        "Two": 2,
        "Three": 3,
        "Four": 4,
        "Five": 5
    }
    return ratings_map.get(rating_str, 0)


def parse_book(article, book_url):
    """
    Extrai os dados principais do livro a partir do elemento HTML do artigo e da URL do livro.
    Retorna um dicionário com as informações estruturadas.
    """
    titulo = article.h3.a["title"]
    preco = article.find("p", class_="price_color").text.replace("£", "")
    disponibilidade = article.find(
        "p", class_="instock availability").text.strip()

    # Converte a classe de rating para número
    rating_class = article.find("p", class_="star-rating")["class"][1]
    rating = parse_rating(rating_class)

    # Monta a URL completa da imagem
    image_relative = article.find("img")["src"]
    imagem = urljoin(BASE_URL, image_relative)

    # Acessa a página individual do livro para extrair a categoria
    soup = get_soup(book_url)
    try:
        categoria = soup.select("ul.breadcrumb li a")[-1].text.strip()
    except Exception as e:
        logger.warning(f"Erro ao extrair categoria do livro {titulo}: {e}")
        categoria = "Unknown"

    return {
        "titulo": titulo,
        "preco": float(preco),
        "rating": rating,
        "disponibilidade": disponibilidade,
        "categoria": categoria,
        "imagem": imagem,
        "url": book_url
    }


def scrape_books(max_pages: int | None = None):
    """
    Função principal que percorre todas as páginas do site (ou até max_pages)
    e coleta dados de todos os livros encontrados.
    Salva o resultado em um CSV em data/books.csv.
    """
    logger.info("Iniciando scraping de livros...")
    BOOKS = []
    page = 1

    while True:
        # Se limite de páginas for atingido, interrompe o loop
        if max_pages is not None and page > max_pages:
            logger.info(f"Limite de páginas atingido: {max_pages}")
            break

        page_url = f"{BASE_URL}catalogue/page-{page}.html"
        soup = get_soup(page_url)

        if not soup:
            logger.warning(f"Não foi possível acessar a página {page}")
            break

        articles = soup.select("article.product_pod")
        if not articles:
            logger.warning(f"Nenhum artigo encontrado na página {page}")
            break

        logger.debug(f"Página {page} - Livros encontrados: {len(articles)}")

        for article in articles:
            relative_url = article.h3.a["href"]
            book_url = urljoin(BASE_URL + "catalogue/", relative_url)

            try:
                data = parse_book(article, book_url)
                BOOKS.append(data)
            except Exception as e:
                logger.error(f"Erro ao processar livro em {book_url}: {e}")

            sleep(0.1)  # Pequeno delay entre requisições

        page += 1

    # Salva os dados em CSV
    df = pd.DataFrame(BOOKS)
    os.makedirs("data", exist_ok=True)
    df.to_csv("data/books.csv", index=False)

    logger.success(
        f"Scraping finalizado! Total de livros coletados: {len(BOOKS)}")
    return BOOKS


if __name__ == "__main__":
    # Executa o scraper coletando todas as páginas disponíveis
    scrape_books(
        max_pages=None
    )
