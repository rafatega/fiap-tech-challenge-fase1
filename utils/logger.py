from loguru import logger
import sys

logger.remove()

logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{module}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="DEBUG",  # MUDAR PARA INFO EM PRODUÇÃO
    enqueue=True,
    backtrace=True,
    diagnose=True
)
