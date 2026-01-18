import os
from typing import Optional
from threading import Lock

import pandas as pd
from fastapi import APIRouter, Query, BackgroundTasks, HTTPException, Depends

from scripts.scraper import scrape_books
from utils.logger import logger
from .auth import require_admin
from .state import set_books_db

router = APIRouter(prefix="/api/v1/scraping", tags=["scraping"])

SCRAPING_LOCK = Lock()
SCRAPING_RUNNING = False


def _do_scrape_and_reload(max_pages: Optional[int] = None) -> None:
    """
    Executa o scraping em background:
    - raspa os livros
    - garante IDs
    - salva no CSV
    - atualiza a base em memória (state)
    """
    global SCRAPING_RUNNING

    try:
        logger.info(f"Scraping iniciado em background (max_pages={max_pages})")

        books = scrape_books(max_pages=max_pages)

        # garante IDs
        for idx, book in enumerate(books, start=1):
            book["id"] = idx

        # salva CSV
        os.makedirs("data", exist_ok=True)
        pd.DataFrame(books).to_csv("data/books.csv", index=False)

        # atualiza memória
        set_books_db(books)

        logger.success(f"Scraping concluído. {len(books)} livros atualizados.")
    except Exception as e:
        logger.exception(f"Erro durante scraping: {e}")
    finally:
        SCRAPING_RUNNING = False


@router.post(
    "/trigger",
    summary="Dispara scraping (ADMIN)",
    description="Dispara o scraping em background. Apenas usuários ADMIN podem acessar.",
)
def trigger_scraping(
    background_tasks: BackgroundTasks,
    max_pages: Optional[int] = Query(
        None, ge=1, description="Limite de páginas para raspar (opcional)"),
    _: dict = Depends(require_admin),
):
    """
    Endpoint que dispara o scraping em background.
    - Usa lock para evitar execuções simultâneas
    - Permite limitar o número de páginas via query param
    """
    logger.info("Requisição recebida para disparar scraping.")
    global SCRAPING_RUNNING

    with SCRAPING_LOCK:
        if SCRAPING_RUNNING:
            raise HTTPException(
                status_code=409, detail="Scraping já está em execução")
        SCRAPING_RUNNING = True

    background_tasks.add_task(_do_scrape_and_reload, max_pages)
    logger.info("Scraping foi disparado via endpoint.")

    return {"status": "accepted", "message": "Scraping disparado em background"}
