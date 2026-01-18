from typing import List, Optional, Dict
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
    items: List[Book] = Field(..., description="Lista de livros encontrados")


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
    count: int = Field(..., example=150)
    min_price: float = Field(..., example=12.34)
    max_price: float = Field(..., example=99.99)
    avg_price: float = Field(..., example=35.67)
    total_price: float = Field(..., example=12345.67)


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
    access_token: str = Field(...,
                              example="eyJhbGciOiJIUzI1NiIsInR5cOiIkpXVCJ9...")
    refresh_token: str = Field(...,
                               example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    expires_in: int = Field(..., example=900)


class RefreshRequest(BaseModel):
    """
    Requisição de renovação do token de acesso.
    """
    refresh_token: str = Field(...,
                               example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")


class UserOut(BaseModel):
    """
    Informações do usuário autenticado.
    """
    username: str = Field(..., example="admin")
    role: str = Field(..., example="admin")

# MACHINE LEARNING MODELS


class MLFeatureItem(BaseModel):
    """
    Representa as features usadas para treinamento ou predição.
    """
    id: int = Field(..., example=10, description="ID do livro (rastreamento)")
    categoria: str = Field(..., example="Poetry")
    in_stock: int = Field(..., ge=0, le=1, example=1)
    rating: int = Field(..., ge=0, le=5, example=4)


class MLFeatureVector(BaseModel):
    categoria: str = Field(..., example="Poetry")
    in_stock: int = Field(..., ge=0, le=1, example=1)
    rating: int = Field(..., ge=0, le=5, example=4)


class MLTrainingDataResponse(BaseModel):
    """
    Dataset formatado para treinamento de modelo ML.
    """
    X: List[MLFeatureVector] = Field(...,
                                     description="Features para treinamento")
    y: List[float] = Field(..., description="Label (preco) para treinamento")


class MLPredictionRequest(BaseModel):
    """
    Payload esperado para envio de predições.
    """
    book_id: int = Field(..., example=10)
    prediction: float = Field(..., example=42.90, description="Preço previsto")
    model_name: Optional[str] = Field(None, example="baseline-v1")


class MLPredictionResponse(BaseModel):
    """
    Resposta após registro de predições.
    """
    status: str = Field(..., example="ok")
    saved: MLPredictionRequest = Field(..., description="Predição registrada")

# MÉTRICAS DA API


class LatencySummary(BaseModel):
    count: int = Field(..., example=1200)
    avg_ms: float = Field(..., example=12.34)
    p50_ms: float = Field(..., example=10.0)
    p95_ms: float = Field(..., example=35.0)
    p99_ms: float = Field(..., example=80.0)
    min_ms: float = Field(..., example=1.2)
    max_ms: float = Field(..., example=250.5)


class TopRouteItem(BaseModel):
    route: str = Field(..., example="/api/v1/books/{id}")
    count: int = Field(..., example=420)


class MetricsResponse(BaseModel):
    uptime_seconds: int = Field(..., example=3600)
    in_flight: int = Field(..., example=0)
    total_requests: int = Field(..., example=5000)
    by_status: Dict[str, int] = Field(..., example={
                                      "2xx": 4900, "4xx": 80, "5xx": 20})
    top_routes: List[TopRouteItem] = Field(...,
                                           description="Rotas mais acessadas")
    latency_overall: LatencySummary = Field(...,
                                            description="Resumo de latência geral")
    latency_by_route: Dict[str, LatencySummary] = Field(...,
                                                        description="Resumo de latência por rota")
