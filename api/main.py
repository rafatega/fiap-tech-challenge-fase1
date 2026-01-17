import os
from fastapi import FastAPI, Query, BackgroundTasks, HTTPException
from typing import Optional, List, Dict
import pandas as pd
from pydantic import BaseModel, Field
from scripts.scraper import scrape_books

# Para rodar corretamente: python -m uvicorn api.main:app --reload na pasta raiz do projeto

app = FastAPI(
    title="API Tech Challenge - Fase 1",
    version="1.0.0",
    description="API para scraping de livros"
)


class Book(BaseModel):
    id: int = Field(..., example=1)
    titulo: str = Field(..., example="A Light in the Attic")
    preco: float = Field(..., example=51.77)
    rating: int = Field(..., ge=0, le=5, example=3)
    disponibilidade: str = Field(..., example="In stock")
    categoria: str = Field(..., example="Poetry")
    imagem: str = Field(...,
                        example="https://books.toscrape.com/media/cache/...")
    url: str = Field(..., example="https://books.toscrape.com/catalogue/...")


class SearchResponse(BaseModel):
    total: int = Field(..., example=2)
    items: List[Book]


class HealthResponse(BaseModel):
    status: str = Field(..., example="ok")
    books_loaded: int = Field(..., example=1000)

# Classe para estatísticas gerais (/api/v1/stats/overview)


class StatsOverviewResponse(BaseModel):
    total_livros: int = Field(..., example=1000)
    preco_medio: float = Field(..., example=35.67)
    distribuicao_ratings: dict[int, int] = Field(..., example={
                                                 1: 123, 2: 456, 3: 321, 4: 90, 5: 10})

# Classe para estatísticas por categoria (/api/v1/stats/categories)


class CategoryStatsItem(BaseModel):
    count: int
    min_price: float
    max_price: float
    avg_price: float
    total_price: float


BOOKS_DB: list[dict] = []


def load_books_from_csv(path: str = "data/books.csv") -> list[dict]:
    if not os.path.exists(path):
        return []
    df = pd.read_csv(path)
    if "id" in df.columns:
        df["id"] = df["id"].astype(int)
    return df.to_dict(orient="records")


@app.on_event("startup")
def load_data():
    global BOOKS_DB

    books = load_books_from_csv("data/books.csv")

    # Se não existe CSV (ou está vazio), faz scraping
    if not books:
        books = scrape_books(max_pages=None)

    # GARANTE ID SEMPRE (mesmo vindo do CSV)
    if len(books) > 0 and "id" not in books[0]:
        for idx, book in enumerate(books, start=1):
            book["id"] = idx

        os.makedirs("data", exist_ok=True)
        pd.DataFrame(books).to_csv("data/books.csv", index=False)

    BOOKS_DB = books


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
