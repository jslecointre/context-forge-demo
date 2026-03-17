import os

from backend.logger import logger
from backend.utils import create_model


QA_MODEL = os.getenv("MODEL", "ibm:openai/gpt-oss-120b")
MAX_TOKEN_WRITER_MODEL = 32000
MAX_TOKEN_SUPERVISOR = None

try:
    logger.info("=" * 50)
    logger.info(f"USING {QA_MODEL.lower()} MODEL")
    logger.info("=" * 50)

    qa_model = create_model(QA_MODEL)

    logger.info("=" * 50)
    logger.info("All models initialized successfully!")
    logger.info("=" * 50)
except Exception as e:
    logger.info(f"Error creating models: {e}")
    raise e
