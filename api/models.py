from typing import List, Dict
from pydantic import BaseModel, Field

# Todos os base models.


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


# AUTH
class LoginRequest(BaseModel):
    username: str = Field(..., example="admin")
    password: str = Field(..., example="admin123")


class TokenResponse(BaseModel):
    token_type: str = Field("bearer", example="bearer")
    access_token: str
    refresh_token: str
    expires_in: int = Field(..., example=900)


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    username: str
    role: str


class TriggerResponse(BaseModel):
    status: str = Field(..., example="accepted")
    message: str = Field(..., example="Scraping disparado em background")
