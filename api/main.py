import os
from fastapi import FastAPI, Query, BackgroundTasks, HTTPException
from typing import Optional, List
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
    imagem: str = Field(..., example="https://books.toscrape.com/media/cache/...")
    url: str = Field(..., example="https://books.toscrape.com/catalogue/...")

class SearchResponse(BaseModel):
    total: int = Field(..., example=2)
    items: List[Book]

class HealthResponse(BaseModel):
    status: str = Field(..., example="ok")
    books_loaded: int = Field(..., example=1000)

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
        books = scrape_books(max_pages=1)

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

