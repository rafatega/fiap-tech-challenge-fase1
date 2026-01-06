import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin
from time import sleep
from utils.logger import logger

# python -m scripts.scraper para rodar o scraper como um módulo, garantindo que as importações funcionem corretamente.

BASE_URL = "https://books.toscrape.com/"
BOOKS = []


def get_soup(url):
    try:
        response = requests.get(url)
        if response.status_code == 404:
            logger.info(f"Fim das páginas! Página não encontrada: {url}")
            return None
        response.raise_for_status()
        return BeautifulSoup(response.content, "html.parser")
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao acessar {url}: {e}")
        return None


def parse_rating(rating_str):
    ratings_map = {
        "One": 1,
        "Two": 2,
        "Three": 3,
        "Four": 4,
        "Five": 5
    }
    return ratings_map.get(rating_str, 0)


def parse_book(article, book_url):
    titulo = article.h3.a["title"]
    preco = article.find("p", class_="price_color").text.replace("£", "")
    disponibilidade = article.find(
        "p", class_="instock availability").text.strip()
    rating_class = article.find("p", class_="star-rating")["class"][1]
    rating = parse_rating(rating_class)
    image_relative = article.find("img")["src"]
    imagem = urljoin(BASE_URL, image_relative)

    # Para pegar categoria, precisamos ir até a página do livro
    soup = get_soup(book_url)
    try:
        categoria = soup.select("ul.breadcrumb li a")[-1].text.strip()
    except Exception:
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


def scrape_books():
    logger.info("Iniciando scraping de livros...")
    page = 1

    while True:
        page_url = f"{BASE_URL}catalogue/page-{page}.html"
        soup = get_soup(page_url)

        if not soup:
            break

        articles = soup.select("article.product_pod")
        if not articles:
            break  # Fim das páginas

        logger.info(f"Página {page}")

        for article in articles:
            relative_url = article.h3.a["href"]
            book_url = urljoin(BASE_URL + "catalogue/", relative_url)
            data = parse_book(article, book_url)
            BOOKS.append(data)
            sleep(0.1)  # Sleep para evitar sobrecarga no servidor

        page += 1

    logger.success(f"Scraping finalizado. Total de livros: {len(BOOKS)}")
    df = pd.DataFrame(BOOKS)
    df.to_csv("data/books.csv", index=False)
    logger.success("Arquivo salvo em data/books.csv")


if __name__ == "__main__":
    scrape_books()
