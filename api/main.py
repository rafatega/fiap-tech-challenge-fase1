from fastapi import FastAPI, Query, BackgroundTasks, HTTPException
from typing import Optional
from scripts.scraper import scrape_books

# Para rodar corretamente: python -m uvicorn api.main:app --reload na pasta raiz do projeto

app = FastAPI(
    title="Api scraper",
    version="1.0.0",
    description="API para scraping de livros"
)

BOOKS_DB: list[dict] = []

@app.on_event("startup")
def load_data():
    global BOOKS_DB
    books = scrape_books(max_pages=1)
    for idx, book in enumerate(books, start=1):
        book["id"] = idx
    BOOKS_DB = books

"""
def run_scraper_bg(max_pages: int):
    scrape_books(max_pages=max_pages)

 @app.get("/scrape")
def scrape(max_pages: int = Query(1, ge=1, le=100)):
    books = scrape_books(max_pages=max_pages)
    return {
        "pages": max_pages,
        "total": len(books),
        "items": books
    }
    
@app.post("/scrape/background")
def scrape_background(
    background_tasks: BackgroundTasks,
    max_pages: int = 1
):
    background_tasks.add_task(run_scraper_bg, max_pages)
    return {
        "status": "scraping started",
        "max_pages": max_pages
    }
 """
@app.get("/api/v1/health")
def health():
    return {
        "status": "ok",
        "books_loaded": len(BOOKS_DB)
    }

@app.get("/api/v1/books")
def get_books():
    return BOOKS_DB

@app.get("/api/v1/books/search")
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

@app.get("/api/v1/books/{id}")
def get_book_by_id(id: int):
    for book in BOOKS_DB:
        if book["id"] == id:
            return book
    raise HTTPException(status_code=404, detail="Livro não encontrado")

