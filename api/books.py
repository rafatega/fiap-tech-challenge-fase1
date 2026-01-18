from threading import Lock
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException, Depends

from .state import get_books_db
from .models import Book, SearchResponse
from utils.logger import logger  # Logger central do projeto

router = APIRouter(prefix="/api/v1/books", tags=["books"])


@router.get("/", tags=["books"], response_model=List[Book])
def get_books():
    """Retorna todos os livros disponíveis na base."""
    logger.info("Listagem de todos os livros solicitada.")
    return get_books_db()


@router.get("/categories", response_model=List[str])
def get_categories():
    """Lista única e ordenada das categorias dos livros."""
    logger.info("Listagem de categorias solicitada.")
    BOOKS_DB = get_books_db()
    categories = sorted({book["categoria"] for book in BOOKS_DB})
    logger.debug(f"Categorias encontradas: {categories}")
    return categories


@router.get("/search", response_model=SearchResponse)
def search_books(title: Optional[str] = Query(None), category: Optional[str] = Query(None)):
    """
    Busca por livros contendo o título informado e/ou categoria exata.
    """
    logger.info("Busca de livros solicitada.")
    results = get_books_db()

    if title:
        results = [b for b in results if title.lower() in b["titulo"].lower()]
        logger.debug(f"Filtro aplicado por título: '{title}'")

    if category:
        results = [b for b in results if category.lower() ==
                   b["categoria"].lower()]
        logger.debug(f"Filtro aplicado por categoria: '{category}'")

    return {"total": len(results), "items": results}


@router.get("/top-rated", response_model=List[Book])
def get_top_rated_books():
    """Retorna todos os livros com a melhor avaliação da base."""
    logger.info("Consulta de livros top-rated solicitada.")
    BOOKS_DB = get_books_db()
    if not BOOKS_DB:
        logger.warning("Nenhum livro disponível para top-rated.")
        return []

    max_rating = max(book["rating"] for book in BOOKS_DB)
    logger.debug(f"Melhor avaliação encontrada: {max_rating}")
    return [book for book in BOOKS_DB if book["rating"] == max_rating]


@router.get("/price-range", response_model=List[Book])
def get_books_by_price_range(
    min: Optional[float] = Query(None, ge=0),
    max: Optional[float] = Query(None, ge=0),
):
    """
    Filtra livros por faixa de preço (mínimo e/ou máximo).
    """
    logger.info("Consulta de livros por faixa de preço solicitada.")
    results = get_books_db()
    if min is not None:
        results = [b for b in results if b["preco"] >= min]
    if max is not None:
        results = [b for b in results if b["preco"] <= max]
    logger.debug(f"Faixa de preço aplicada: min={min}, max={max}")

    return results


@router.get("/{id}", response_model=Book)
def get_book_by_id(id: int):
    """Busca livro pelo ID fornecido."""
    logger.info(f"Consulta de livro por ID solicitada: {id}")
    BOOKS_DB = get_books_db()
    for book in BOOKS_DB:
        if book["id"] == id:
            logger.info(f"Livro encontrado: {book}")
            return book

    logger.warning(f"Livro com ID {id} não encontrado.")
    raise HTTPException(status_code=404, detail="Livro não encontrado")
