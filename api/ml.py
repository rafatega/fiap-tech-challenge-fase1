from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException

from .models import MLFeatureItem, MLTrainingDataResponse, MLPredictionRequest, MLPredictionResponse

router = APIRouter(prefix="/api/v1/ml", tags=["ml"])

# “banco” simples em memória para armazenar predições recebidas
PREDICTIONS_DB: list[dict] = []


def _to_in_stock(disponibilidade: str) -> int:
    if not disponibilidade:
        return 0
    return 1 if "in stock" in disponibilidade.lower() else 0


@router.get(
    "/features",
    summary="Dados formatados para features",
    description="Retorna features (X) prontas para consumo por modelos ML.",
    response_model=List[MLFeatureItem],
)
def get_ml_features():
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
    description="Retorna X (features) e y (preco) para treinamento de modelo.",
    response_model=MLTrainingDataResponse,
)
def get_ml_training_data():
    from .main import BOOKS_DB

    X = [
        MLFeatureItem(
            # referência, não precisa usar como feature no modelo
            id=int(b["id"]),
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
    description="Recebe e registra predições geradas por um modelo ML.",
    response_model=MLPredictionResponse,
)
def post_ml_predictions(payload: MLPredictionRequest):
    from .main import BOOKS_DB

    exists = any(b.get("id") == payload.book_id for b in BOOKS_DB)
    if not exists:
        raise HTTPException(
            status_code=404, detail="Livro não encontrado para o book_id informado")

    record = payload.model_dump()
    record["created_at"] = datetime.utcnow().isoformat()
    PREDICTIONS_DB.append(record)

    return {"status": "ok", "saved": payload}
