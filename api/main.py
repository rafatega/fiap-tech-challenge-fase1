import os
from fastapi import FastAPI, Query, BackgroundTasks, HTTPException, Depends
from typing import Optional, List, Dict
import pandas as pd
from scripts.scraper import scrape_books
from threading import Lock

from .models import Book, SearchResponse, HealthResponse, StatsOverviewResponse, CategoryStatsItem
from .auth import router as auth_router, ensure_default_users, init_auth_db, require_admin

# Para rodar corretamente: python -m uvicorn api.main:app --reload na pasta raiz do projeto

app = FastAPI(
    title="API Tech Challenge - Fase 1",
    version="1.0.0",
    description="API para scraping de livros"
)

# Inicializa o banco de dados de autenticação e cria usuários padrão
app.include_router(auth_router)

BOOKS_DB: list[dict] = []

SCRAPING_LOCK = Lock()
SCRAPING_RUNNING = False


def load_books_from_csv(path: str = "data/books.csv") -> list[dict]:
    if not os.path.exists(path):
        return []
    df = pd.read_csv(path)
    if "id" in df.columns:
        df["id"] = df["id"].astype(int)
    return df.to_dict(orient="records")


def _do_scrape_and_reload(max_pages: Optional[int] = None) -> None:
    """
    Roda scraping, garante IDs, salva CSV e atualiza BOOKS_DB.
    """
    global BOOKS_DB, SCRAPING_RUNNING

    try:
        # seu scraper já salva data/books.csv
        books = scrape_books(max_pages=max_pages)

        # garante id (o scraper não gera id)
        for idx, book in enumerate(books, start=1):
            book["id"] = idx

        # sobrescreve o CSV agora COM id (pra ficar consistente com sua API)
        os.makedirs("data", exist_ok=True)
        pd.DataFrame(books).to_csv("data/books.csv", index=False)

        BOOKS_DB = books
    finally:
        SCRAPING_RUNNING = False


@app.on_event("startup")
def load_data():
    global BOOKS_DB

    # Inicializa o banco de autenticação e cria usuários padrão
    init_auth_db()
    ensure_default_users()

    books = load_books_from_csv("data/books.csv")

    # Se não existe CSV, carrega lista vazia (o scraper só pode ser disparado via API com permissão de admin)
    if not books:
        books = []

    # GARANTE ID SEMPRE (mesmo vindo do CSV)
    if len(books) > 0 and "id" not in books[0]:
        for idx, book in enumerate(books, start=1):
            book["id"] = idx

        os.makedirs("data", exist_ok=True)
        pd.DataFrame(books).to_csv("data/books.csv", index=False)

    BOOKS_DB = books


@app.post(
    "/api/v1/scraping/trigger",
    tags=["scraping"],
    summary="Dispara scraping (ADMIN)",
    description="Dispara o scraping em background e atualiza o CSV e a base em memória (somente ADMIN).",
)
def trigger_scraping(
    background_tasks: BackgroundTasks,
    max_pages: Optional[int] = Query(None, ge=1),
    _: dict = Depends(require_admin),
):
    global SCRAPING_RUNNING

    # evita duas execuções simultâneas
    with SCRAPING_LOCK:
        if SCRAPING_RUNNING:
            raise HTTPException(
                status_code=409, detail="Scraping já está em execução")
        SCRAPING_RUNNING = True

    background_tasks.add_task(_do_scrape_and_reload, max_pages)
    return {"status": "accepted", "message": "Scraping disparado em background"}


@app.get(
    "/api/v1/health",
    tags=["health"],
    summary="Verifica o status da API",
    description="Verifica se a API está ativa e quantos livros estão carregados na base.",
    response_model=HealthResponse
)
def health():
    return {
        "status": "ok",
        "books_loaded": len(BOOKS_DB)
    }


@app.get(
    "/api/v1/books",
    tags=["books"],
    summary="Lista todos os livros",
    description="Lista todos os livros disponíveis na base.",
    response_model=List[Book]
)
def get_books():
    return BOOKS_DB


@app.get(
    "/api/v1/categories",
    tags=["categories"],
    summary="Lista as categorias dos livros",
    description="Retorna uma lista única e ordenada das categorias disponíveis.",
    response_model=List[str],
)
def get_categories():
    categories = sorted(
        {book["categoria"] for book in BOOKS_DB}
    )
    return categories


@app.get(
    "/api/v1/books/search",
    tags=["books"],
    summary="Busca livros por título e/ou categoria",
    description="Busca livros por trecho do título (contém) e/ou categoria (exata).",
    response_model=SearchResponse
)
def search_books(
    title: Optional[str] = Query(None),
    category: Optional[str] = Query(None)
):
    results = BOOKS_DB

    if title:
        results = [
            b for b in results
            if title.lower() in b["titulo"].lower()
        ]

    if category:
        results = [
            b for b in results
            if category.lower() == b["categoria"].lower()
        ]

    return {
        "total": len(results),
        "items": results
    }


@app.get(
    "/api/v1/books/top-rated",
    tags=["books"],
    summary="Lista os livros com melhor avaliação",
    description="Retorna todos os livros com o rating mais alto da base.",
    response_model=List[Book]
)
def get_top_rated_books():
    if not BOOKS_DB:
        return []

    max_rating = max(book["rating"] for book in BOOKS_DB)
    top_books = [book for book in BOOKS_DB if book["rating"] == max_rating]

    return top_books


@app.get(
    "/api/v1/books/price-range",
    tags=["books"],
    summary="Filtra livros por faixa de preço",
    description="Retorna livros com preço entre os valores mínimos e máximos informados.",
    response_model=List[Book]
)
def get_books_by_price_range(
    min: Optional[float] = Query(None, ge=0),
    max: Optional[float] = Query(None, ge=0)
):
    results = BOOKS_DB

    if min is not None:
        results = [book for book in results if book["preco"] >= min]

    if max is not None:
        results = [book for book in results if book["preco"] <= max]

    return results


@app.get(
    "/api/v1/books/{id}",
    tags=["books"],
    summary="Consulta os livros pelo ID",
    description="Retorna os detalhes completos de um livro específico pelo ID.",
    response_model=Book,
    responses={
        404: {
            "description": "Livro não encontrado",
            "content": {
                "application/json": {
                    "example": {"detail": "Livro não encontrado"}
                }
            },
        }
    },
)
def get_book_by_id(id: int):
    for book in BOOKS_DB:
        if book["id"] == id:
            return book
    raise HTTPException(status_code=404, detail="Livro não encontrado")


@app.get(
    "/api/v1/stats/overview",
    tags=["stats"],
    summary="Estatísticas gerais dos livros",
    description="Retorna o total de livros, o preço médio e a distribuição de ratings.",
    response_model=StatsOverviewResponse
)
def get_stats_overview():
    if not BOOKS_DB:
        return {
            "total_livros": 0,
            "preco_medio": 0.0,
            "distribuicao_ratings": {}
        }

    total_livros = len(BOOKS_DB)
    preco_medio = round(sum(b["preco"] for b in BOOKS_DB) / total_livros, 2)

    distribuicao_ratings = {}
    for b in BOOKS_DB:
        rating = b.get("rating", 0)
        distribuicao_ratings[rating] = distribuicao_ratings.get(rating, 0) + 1

    return {
        "total_livros": total_livros,
        "preco_medio": preco_medio,
        "distribuicao_ratings": distribuicao_ratings
    }


@app.get(
    "/api/v1/stats/categories",
    tags=["stats"],
    summary="Estatísticas por categoria",
    description="Retorna estatísticas detalhadas por categoria: quantidade de livros e dados de preços.",
    response_model=Dict[str, CategoryStatsItem]
)
def get_stats_by_category():
    if not BOOKS_DB:
        return {}

    from collections import defaultdict
    import numpy as np

    stats = defaultdict(lambda: {"count": 0, "total_price": 0.0, "prices": []})

    for book in BOOKS_DB:
        categoria = book.get("categoria", "Desconhecida")
        preco = book.get("preco", 0.0)

        try:
            preco = float(preco)
        except (ValueError, TypeError):
            preco = 0.0

        stats[categoria]["count"] += 1
        stats[categoria]["total_price"] += preco
        stats[categoria]["prices"].append(preco)

    return {
        categoria: CategoryStatsItem(
            count=data["count"],
            min_price=round(min(data["prices"]), 2),
            max_price=round(max(data["prices"]), 2),
            avg_price=round(np.mean(data["prices"]), 2),
            total_price=round(data["total_price"], 2),
        )
        for categoria, data in stats.items()
    }
