from fastapi import FastAPI, Query
from scripts.scraper import scrape_books

app = FastAPI(
    title="Api scraper",
    version="1.0.0",
    description="API para scraping de livros"
)

@app.get("/scrape")
def scrape(max_pages: int = Query(1, ge=1, le=100)):
    books = scrape_books(max_pages=max_pages)
    return {
        "pages": max_pages,
        "total": len(books),
        "items": books
    }