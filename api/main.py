import os
from fastapi import FastAPI, Query, BackgroundTasks, HTTPException, Depends
from typing import Optional, List, Dict
import pandas as pd
import numpy as np
from scripts.scraper import scrape_books
from threading import Lock
from collections import defaultdict

from utils.logger import logger  # Logger central do projeto
from .models import Book, SearchResponse, HealthResponse, StatsOverviewResponse, CategoryStatsItem
from .auth import router as auth_router, ensure_default_users, init_auth_db, require_admin
from .ml import router as ml_router
from .metrics import router as metrics_router, MetricsMiddleware

# Para rodar corretamente: python -m uvicorn api.main:app --reload na pasta raiz do projeto

app = FastAPI(
    title="API Tech Challenge - Fase 1",
    version="1.0.2",
    description="API para scraping de livros"
)

# Roteador de autenticação
app.include_router(auth_router)

# Roteador de ML
app.include_router(ml_router)

# Roteador de métricas + middleware
app.include_router(metrics_router)
app.add_middleware(MetricsMiddleware)

BOOKS_DB: list[dict] = []  # Base em memória (é recarregada na inicialização)

SCRAPING_LOCK = Lock()  # Lock para evitar múltiplas execuções simultâneas
SCRAPING_RUNNING = False


def load_books_from_csv(path: str = "data/books.csv") -> list[dict]:
    """
    Carrega os livros de um CSV local e retorna como lista de dicionários.
    """
    logger.info(f"Carregando livros do CSV: {path}")
    if not os.path.exists(path):
        logger.warning(
            f"Arquivo {path} não encontrado. Carregando base vazia.")
        return []

    df = pd.read_csv(path)

    if "id" in df.columns:
        df["id"] = df["id"].astype(int)

    logger.info(f"{len(df)} livros carregados de {path}")
    return df.to_dict(orient="records")


def _do_scrape_and_reload(max_pages: Optional[int] = None) -> None:
    """
    Executa o scraping, adiciona IDs, atualiza CSV e carrega a base em memória.
    Roda em background.
    """
    logger.info("Iniciando scraping em background...")
    global BOOKS_DB, SCRAPING_RUNNING

    try:
        logger.info("Scraping iniciado em background...")
        books = scrape_books(max_pages=max_pages)

        for idx, book in enumerate(books, start=1):
            book["id"] = idx

        pd.DataFrame(books).to_csv("data/books.csv", index=False)
        BOOKS_DB = books

        logger.success(
            f"Scraping concluído. {len(books)} livros atualizados.")
    except Exception as e:
        logger.exception(f"❌ Erro durante scraping: {e}")
    finally:
        SCRAPING_RUNNING = False


@app.on_event("startup")
def load_data():
    """
    Executado automaticamente ao subir a API.
    - Inicializa o banco de autenticação
    - Cria usuários padrão
    - Carrega livros do CSV para a base em memória
    """
    logger.info("Inicializando API e carregando dados...")
    global BOOKS_DB

    init_auth_db()
    ensure_default_users()

    books = load_books_from_csv("data/books.csv")

    # Garante IDs únicos se ausentes
    if books and "id" not in books[0]:
        for idx, book in enumerate(books, start=1):
            book["id"] = idx
        pd.DataFrame(books).to_csv("data/books.csv", index=False)
        logger.info("IDs adicionados ao CSV.")

    BOOKS_DB = books
    logger.info(f"{len(BOOKS_DB)} livros disponíveis em memória.")


@app.post("/api/v1/scraping/trigger", tags=["scraping"], summary="Dispara scraping (ADMIN)")
def trigger_scraping(
    background_tasks: BackgroundTasks,
    max_pages: Optional[int] = Query(None, ge=1),
    _: dict = Depends(require_admin),
):
    """
    Endpoint que dispara o scraping em background.
    Permite definir limite de páginas (opcional).
    Apenas usuários ADMIN podem acessar.
    """
    logger.info("Requisição recebida para disparar scraping.")
    global SCRAPING_RUNNING

    with SCRAPING_LOCK:
        if SCRAPING_RUNNING:
            raise HTTPException(
                status_code=409, detail="Scraping já está em execução"
            )
        SCRAPING_RUNNING = True

    logger.info("Scraping foi disparado via endpoint.")
    background_tasks.add_task(_do_scrape_and_reload, max_pages)

    return {"status": "accepted", "message": "Scraping disparado em background"}


@app.get("/api/v1/health", tags=["health"], response_model=HealthResponse)
def health():
    """Verifica se a API está online e quantos livros estão carregados."""
    logger.info("Health check solicitado.")
    return {"status": "ok", "books_loaded": len(BOOKS_DB)}


@app.get("/api/v1/books", tags=["books"], response_model=List[Book])
def get_books():
    """Retorna todos os livros disponíveis na base."""
    logger.info("Listagem de todos os livros solicitada.")
    return BOOKS_DB


@app.get("/api/v1/categories", tags=["categories"], response_model=List[str])
def get_categories():
    """Lista única e ordenada das categorias dos livros."""
    logger.info("Listagem de categorias solicitada.")
    categories = sorted({book["categoria"] for book in BOOKS_DB})
    logger.debug(f"Categorias encontradas: {categories}")
    return categories


@app.get("/api/v1/books/search", tags=["books"], response_model=SearchResponse)
def search_books(title: Optional[str] = Query(None), category: Optional[str] = Query(None)):
    """
    Busca por livros contendo o título informado e/ou categoria exata.
    """
    logger.info("Busca de livros solicitada.")
    results = BOOKS_DB

    if title:
        results = [b for b in results if title.lower() in b["titulo"].lower()]
        logger.debug(f"Filtro aplicado por título: '{title}'")

    if category:
        results = [b for b in results if category.lower() ==
                   b["categoria"].lower()]
        logger.debug(f"Filtro aplicado por categoria: '{category}'")

    return {"total": len(results), "items": results}


@app.get("/api/v1/books/top-rated", tags=["books"], response_model=List[Book])
def get_top_rated_books():
    """Retorna todos os livros com a melhor avaliação da base."""
    logger.info("Consulta de livros top-rated solicitada.")
    if not BOOKS_DB:
        logger.warning("Nenhum livro disponível para top-rated.")
        return []

    max_rating = max(book["rating"] for book in BOOKS_DB)
    logger.debug(f"Melhor avaliação encontrada: {max_rating}")
    return [book for book in BOOKS_DB if book["rating"] == max_rating]


@app.get("/api/v1/books/price-range", tags=["books"], response_model=List[Book])
def get_books_by_price_range(
    min: Optional[float] = Query(None, ge=0),
    max: Optional[float] = Query(None, ge=0),
):
    """
    Filtra livros por faixa de preço (mínimo e/ou máximo).
    """
    logger.info("Consulta de livros por faixa de preço solicitada.")
    results = BOOKS_DB
    if min is not None:
        results = [b for b in results if b["preco"] >= min]
    if max is not None:
        results = [b for b in results if b["preco"] <= max]
    logger.debug(f"Faixa de preço aplicada: min={min}, max={max}")

    return results


@app.get("/api/v1/books/{id}", tags=["books"], response_model=Book)
def get_book_by_id(id: int):
    """Busca livro pelo ID fornecido."""
    logger.info(f"Consulta de livro por ID solicitada: {id}")
    for book in BOOKS_DB:
        if book["id"] == id:
            logger.info(f"Livro encontrado: {book}")
            return book

    logger.warning(f"Livro com ID {id} não encontrado.")
    raise HTTPException(status_code=404, detail="Livro não encontrado")


@app.get("/api/v1/stats/overview", tags=["stats"], response_model=StatsOverviewResponse)
def get_stats_overview():
    """Estatísticas gerais: total de livros, preço médio e distribuição de ratings."""
    logger.info("Estatísticas gerais solicitadas.")
    if not BOOKS_DB:
        logger.warning("Estatísticas solicitadas com base vazia.")
        return {"total_livros": 0, "preco_medio": 0.0, "distribuicao_ratings": {}}

    total_livros = len(BOOKS_DB)
    preco_medio = round(sum(b["preco"] for b in BOOKS_DB) / total_livros, 2)

    distribuicao_ratings = {}
    for b in BOOKS_DB:
        rating = b.get("rating", 0)
        distribuicao_ratings[rating] = distribuicao_ratings.get(rating, 0) + 1

    return {
        "total_livros": total_livros,
        "preco_medio": preco_medio,
        "distribuicao_ratings": distribuicao_ratings,
    }


@app.get("/api/v1/stats/categories", tags=["stats"], response_model=Dict[str, CategoryStatsItem])
def get_stats_by_category():
    """Estatísticas agregadas por categoria: contagem, preços mínimo/máximo/médio."""
    logger.info("Estatísticas por categoria solicitadas.")
    if not BOOKS_DB:
        logger.warning("Estatísticas por categoria com base vazia.")
        return {}

    stats = defaultdict(lambda: {"count": 0, "total_price": 0.0, "prices": []})

    for book in BOOKS_DB:
        categoria = book.get("categoria", "Desconhecida")
        try:
            preco = float(book.get("preco", 0.0))
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
