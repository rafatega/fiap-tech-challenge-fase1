from fastapi import FastAPI
import pandas as pd
from utils.logger import logger

from .state import load_books_from_csv, set_books_db, get_books_db
from .auth import router as auth_router, init_auth_db, ensure_default_users
from .ml import router as ml_router
from .metrics import router as metrics_router, MetricsMiddleware
from .books import router as books_router
from .stats import router as stats_router
from .scraping import router as scraping_router


app = FastAPI(
    title="API Tech Challenge - Fase 1",
    version="1.0.3",
    description="API para scraping de livros"
)

# Routers
app.include_router(auth_router)
app.include_router(ml_router)
app.include_router(metrics_router)
app.include_router(books_router)
app.include_router(stats_router)
app.include_router(scraping_router)

# Middleware
app.add_middleware(MetricsMiddleware)

# Estado global
books = load_books_from_csv("data/books.csv")


@app.on_event("startup")
def load_data():
    """
    Executado automaticamente ao subir a API.
    - Inicializa o banco de autenticação
    - Cria usuários padrão
    - Carrega livros do CSV para a base em memória (state)
    """
    logger.info("Inicializando API e carregando dados...")

    # Auth
    init_auth_db()
    ensure_default_users()

    # Livros (CSV -> memória)
    books = load_books_from_csv("data/books.csv")

    # Garante IDs únicos se ausentes (mantive seu comportamento)
    if books and "id" not in books[0]:
        for idx, book in enumerate(books, start=1):
            book["id"] = idx
        pd.DataFrame(books).to_csv("data/books.csv", index=False)
        logger.info("IDs adicionados ao CSV.")

    # Salva a base na memória via state
    set_books_db(books)

    logger.info(f"{len(get_books_db())} livros disponíveis em memória.")
