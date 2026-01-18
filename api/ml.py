from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException

from .models import MLFeatureItem, MLFeatureVector, MLTrainingDataResponse, MLPredictionRequest, MLPredictionResponse
from utils.logger import logger

router = APIRouter(prefix="/api/v1/ml", tags=["ml"])

# “banco” simples em memória para armazenar predições recebidas
PREDICTIONS_DB: list[dict] = []


def _to_in_stock(disponibilidade: str) -> int:
    """
    Converte o campo 'disponibilidade' em feature binária:
    - 1 se contém 'in stock'
    - 0 caso contrário
    """
    if not disponibilidade:
        return 0
    return 1 if "in stock" in disponibilidade.lower() else 0


@router.get(
    "/features",
    summary="Dados formatados para features",
    description=(
        "Retorna somente as features (X) em formato adequado para consumo por modelos de ML.\n\n"
        "Features retornadas:\n"
        "- categoria (str)\n"
        "- in_stock (0/1)\n"
        "- rating (0..5)\n\n"
        "Obs.: o 'id' é retornado apenas para rastreabilidade."),
    response_model=List[MLFeatureItem],
)
def get_ml_features():
    """
    Retorna a lista de features (X), uma linha por livro.
    """
    logger.info("Consulta de features para ML solicitada")
    # Import local evita import circular entre routers e main
    from .main import BOOKS_DB

    return [
        MLFeatureItem(
            id=int(b["id"]),
            categoria=str(b.get("categoria", "Unknown")),
            in_stock=_to_in_stock(str(b.get("disponibilidade", ""))),
            rating=int(b.get("rating", 0) or 0),
        )
        for b in BOOKS_DB
    ]


@router.get(
    "/training-data",
    summary="Dataset para treinamento",
    description=(
        "Retorna o dataset completo para treinamento de modelo.\n\n"
        "- X: features (categoria, in_stock, rating)\n"
        "- y: label (preco)\n\n"),
    response_model=MLTrainingDataResponse,
)
def get_ml_training_data():
    """
    Retorna X e y, onde:
    - X: lista de features por livro
    - y: lista de preços (float) correspondentes
    """
    logger.info("Consulta de dataset para treinamento de ML solicitada")
    from .main import BOOKS_DB

    X = [
        MLFeatureVector(
            categoria=str(b.get("categoria", "Unknown")),
            in_stock=_to_in_stock(str(b.get("disponibilidade", ""))),
            rating=int(b.get("rating", 0) or 0),
        )
        for b in BOOKS_DB
    ]

    y = [float(b.get("preco", 0.0) or 0.0) for b in BOOKS_DB]

    return {"X": X, "y": y}


@router.post(
    "/predictions",
    summary="Endpoint para receber predições",
    description=(
        "Recebe predições geradas por um modelo de ML e registra em memória.\n\n"
        "Uso típico:\n"
        "- O cliente (modelo) envia book_id + prediction (ex: preço previsto)\n"
        "- A API valida se o book_id existe e salva o registro.\n"),
    response_model=MLPredictionResponse,
)
def post_ml_predictions(payload: MLPredictionRequest):
    """
    Recebe uma predição e registra em memória (PREDICTIONS_DB).

    Importante:
    - Este endpoint NÃO executa modelo.
    - Ele apenas recebe e armazena a predição enviada pelo cliente.
    """
    logger.info(
        f"Recebida predição para book_id {payload.book_id}: {payload.prediction}")
    from .main import BOOKS_DB

    exists = any(b.get("id") == payload.book_id for b in BOOKS_DB)
    if not exists:
        raise HTTPException(
            status_code=404, detail="Livro não encontrado para o book_id informado")

    record = payload.model_dump()
    record["created_at"] = datetime.utcnow().isoformat()
    PREDICTIONS_DB.append(record)

    return {"status": "ok", "saved": payload}
