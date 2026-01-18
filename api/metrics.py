import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Deque, Dict

from fastapi import APIRouter
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .models import MetricsResponse
from utils.logger import logger

router = APIRouter(prefix="/api/v1/health", tags=["metrics"])


@dataclass
class MetricsStore:
    started_at: float = field(default_factory=time.time)
    in_flight: int = 0

    total_requests: int = 0
    by_route: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    by_status: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

    latencies_ms: Deque[float] = field(
        default_factory=lambda: deque(maxlen=2000))
    route_latencies_ms: Dict[str, Deque[float]] = field(
        default_factory=lambda: defaultdict(lambda: deque(maxlen=500)))

    def observe(self, route: str, status_code: int, latency_ms: float) -> None:
        self.total_requests += 1
        self.by_route[route] += 1

        bucket = f"{status_code // 100}xx"
        self.by_status[bucket] += 1

        self.latencies_ms.append(latency_ms)
        self.route_latencies_ms[route].append(latency_ms)


STORE = MetricsStore()


def _percentile(values, p: float) -> float:
    """
    Calcula o percentil p (0.0..1.0) da lista de valores.
    """
    if not values:
        return 0.0
    s = sorted(values)
    k = int(round((len(s) - 1) * p))
    return float(s[k])


def _summary(values) -> dict:
    """
    Gera resumo estatístico simples (count, avg, p50, p95, p99, min, max).
    """
    if not values:
        return {"count": 0, "avg_ms": 0.0, "p50_ms": 0.0, "p95_ms": 0.0, "p99_ms": 0.0, "min_ms": 0.0, "max_ms": 0.0}
    vals = list(values)
    return {
        "count": len(vals),
        "avg_ms": round(sum(vals) / len(vals), 2),
        "p50_ms": round(_percentile(vals, 0.50), 2),
        "p95_ms": round(_percentile(vals, 0.95), 2),
        "p99_ms": round(_percentile(vals, 0.99), 2),
        "min_ms": round(min(vals), 2),
        "max_ms": round(max(vals), 2),
    }


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        STORE.in_flight += 1

        status_code = 500
        try:
            response: Response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            STORE.in_flight -= 1

            route = request.url.path
            if request.scope.get("route") and getattr(request.scope["route"], "path", None):
                route = request.scope["route"].path  # ex: /api/v1/books/{id}

            STORE.observe(route=route, status_code=status_code,
                          latency_ms=elapsed_ms)


@router.get(
    "/performance",
    summary="Métricas de performance da API",
    description="Retorna métricas simples (contadores e latência) coletadas via middleware.",
    response_model=MetricsResponse,
)
def get_metrics():
    """
    Retorna as métricas coletadas pelo middleware.
    """
    logger.info("Métricas da API solicitadas")
    uptime_s = time.time() - STORE.started_at
    top_routes = sorted(STORE.by_route.items(),
                        key=lambda x: x[1], reverse=True)[:25]

    return {
        "uptime_seconds": int(uptime_s),
        "in_flight": STORE.in_flight,
        "total_requests": STORE.total_requests,
        "by_status": dict(STORE.by_status),
        "top_routes": [{"route": r, "count": c} for r, c in top_routes],
        "latency_overall": _summary(STORE.latencies_ms),
        "latency_by_route": {route: _summary(dq) for route, dq in STORE.route_latencies_ms.items()},
    }
