# logging_setup.py

import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)


logging.getLogger("httpx").setLevel(logging.WARNING)
