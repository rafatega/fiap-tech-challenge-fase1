from typing import List, Optional
from pydantic import BaseModel, Field

# MODELS DE BOOKS


class Book(BaseModel):
    """
    Representa os dados completos de um livro retornado pela API.
    Usado em: múltiplos endpoints de livros.
    """
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
    """
    Resposta padrão para buscas de livros.
    Usado em: /api/v1/books/search
    """
    total: int = Field(..., example=2)
    items: List[Book]


class HealthResponse(BaseModel):
    """
    Modelo usado no endpoint de health check.
    Usado em: /api/v1/health
    """
    status: str = Field(..., example="ok")
    books_loaded: int = Field(..., example=1000)


class StatsOverviewResponse(BaseModel):
    """
    Resumo estatístico geral dos livros disponíveis.
    Usado em: /api/v1/stats/overview
    """
    total_livros: int = Field(..., example=1000)
    preco_medio: float = Field(..., example=35.67)
    distribuicao_ratings: dict[int, int] = Field(..., example={
                                                 1: 123, 2: 456, 3: 321, 4: 90, 5: 10})


class CategoryStatsItem(BaseModel):
    """
    Estatísticas agregadas por categoria.
    Usado em: /api/v1/stats/categories
    """
    count: int
    min_price: float
    max_price: float
    avg_price: float
    total_price: float


class TriggerResponse(BaseModel):
    """
    Resposta do endpoint de trigger do scraping.
    Usado em: /api/v1/scrape/trigger
    """
    status: str = Field(..., example="accepted")
    message: str = Field(..., example="Scraping disparado em background")

# MODELS DE AUTENTICAÇÃO


class LoginRequest(BaseModel):
    """
    Payload esperado para login.
    """
    username: str = Field(..., example="admin")
    password: str = Field(..., example="admin123")


class TokenResponse(BaseModel):
    """
    Retorno do login contendo os tokens JWT.
    """
    token_type: str = Field("bearer", example="bearer")
    access_token: str
    refresh_token: str
    expires_in: int = Field(..., example=900)


class RefreshRequest(BaseModel):
    """
    Requisição de renovação do token de acesso.
    """
    refresh_token: str


class UserOut(BaseModel):
    """
    Informações do usuário autenticado.
    """
    username: str
    role: str

# MACHINE LEARNING MODELS


class MLFeatureItem(BaseModel):
    id: int  # só para referência (não precisa virar feature no modelo)
    categoria: str
    in_stock: int = Field(..., ge=0, le=1)
    rating: int = Field(..., ge=0, le=5)


class MLTrainingDataResponse(BaseModel):
    X: List[MLFeatureItem]
    y: List[float] = Field(..., description="Label (preco) para treinamento")


class MLPredictionRequest(BaseModel):
    book_id: int = Field(..., ge=1, description="ID do livro")
    prediction: int = Field(..., ge=0, le=5,
                            description="Predição (ex: rating previsto 0..5)")
    model_name: Optional[str] = Field(
        None, description="Nome/versão do modelo (opcional)")


class MLPredictionResponse(BaseModel):
    status: str = Field(..., example="ok")
    saved: MLPredictionRequest
