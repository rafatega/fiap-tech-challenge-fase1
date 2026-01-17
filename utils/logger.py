from loguru import logger
import sys

# Remove qualquer configuração pré-existente
logger.remove()

# Nível de log adaptável ao ambiente
LOG_LEVEL = "INFO"

# Adiciona saída padrão com formato customizado
logger.add(
    sys.stdout,
    level=LOG_LEVEL,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{module}</cyan>:<cyan>{function}</cyan> - "
        "<level>{message}</level>"
    ),
    enqueue=True,     # Thread-safe / async-safe
    backtrace=True,   # Mostra o traceback completo se erro acontecer
    diagnose=True     # Diagnóstico detalhado do erro
)

# Salvar em arquivo
logger.add(
    "logs/app.log",
    rotation="1 MB",  # Gira arquivo ao atingir 1MB
    retention="10 days",  # Mantém logs por 10 dias
    compression="zip",    # Comprime arquivos antigos
    level=LOG_LEVEL
)

# Exporta o logger já configurado
__all__ = ["logger"]
