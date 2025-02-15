import os
from pathlib import Path
import logging

class Config:
    SEED = 42
    ALLOWED_FILE_EXTENSIONS = set([".pdf", ".md", ".txt"])

    class Model:
        # NAME = "deepseek-r1:1.5b"
        NAME = "llama3:latest" # llama3 is the best"
        # NAME = "mistral:instruct" so slow
        TEMPERATURE = 0.6

    class Preprocessing:
        CHUNK_SIZE = 2048
        CHUNK_OVERLAP = 128
        EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
        RERANKER = "ms-marco-MiniLM-L-12-v2"
        LLM = "llama3:latest"
        CONTEXTUALIZE_CHUNKS = True
        N_SEMANTIC_RESULTS = 5
        N_BM25_RESULTS = 5

    class Chatbot:
        N_CONTEXT_RESULTS = 3

    class Path:
        APP_HOME = Path(os.getenv("APP_HOME", Path(__file__).parent.parent))
        DATA_DIR = APP_HOME / "data"

    @staticmethod
    def configure_logging():
        logging_config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                },
            },
            'handlers': {
                'console': {
                    'level': 'DEBUG',
                    'class': 'logging.StreamHandler',
                    'formatter': 'standard',
                },
                'file': {
                    'level': 'INFO',
                    'class': 'logging.FileHandler',
                    'filename': 'app.log',
                    'formatter': 'standard',
                },
            },
            'loggers': {
                '': {
                    'handlers': ['console', 'file'],
                    'level': 'DEBUG',
                    'propagate': True,
                },
            },
        }
        logging.config.dictConfig(logging_config)

# Example usage
if __name__ == "__main__":
    Config.configure_logging()
    logger = logging.getLogger(__name__)
    logger.info("Logging configured successfully")
