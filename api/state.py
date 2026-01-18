# api/state.py
import os
from typing import List, Dict

import pandas as pd
from utils.logger import logger

# Base em memória (única fonte em runtime)
BOOKS_DB: List[Dict] = []


def load_books_from_csv(path: str = "data/books.csv") -> List[Dict]:
    """Carrega os livros do CSV e retorna como lista de dicionários."""
    logger.info(f"Carregando livros do CSV: {path}")
    if not os.path.exists(path):
        logger.warning(
            f"Arquivo {path} não encontrado. Carregando base vazia.")
        return []

    df = pd.read_csv(path)
    if "id" in df.columns:
        df["id"] = df["id"].astype(int)

    books = df.to_dict(orient="records")
    logger.info(f"{len(books)} livros carregados de {path}")
    return books


def get_books_db() -> List[Dict]:
    """Retorna a base em memória."""
    return BOOKS_DB


def set_books_db(books: List[Dict]) -> None:
    """Atualiza a base em memória."""
    global BOOKS_DB
    BOOKS_DB = books
