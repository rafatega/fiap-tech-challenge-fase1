from typing import Dict
from collections import defaultdict
from fastapi import APIRouter
import numpy as np

from .state import get_books_db
from .models import StatsOverviewResponse, CategoryStatsItem
from utils.logger import logger

router = APIRouter(prefix="/api/v1/stats", tags=["stats"])


@router.get("/overview", response_model=StatsOverviewResponse)
def get_stats_overview():
    """Estatísticas gerais: total de livros, preço médio e distribuição de ratings."""

    BOOKS_DB = get_books_db()

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


@router.get("/categories", response_model=Dict[str, CategoryStatsItem])
def get_stats_by_category():
    """Estatísticas agregadas por categoria: contagem, preços mínimo/máximo/médio."""

    BOOKS_DB = get_books_db()

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
