# cogvault/__init__.py

# Expose specific classes/functions from the module
from .chatbot import Chatbot, ChunkEvent, Message, Role, SourcesEvent, create_history
from .config import Config
from .data_ingestor import ingest_files
from .file_loader import File, load_uploaded_file

# Optional: Define what gets imported when using `from cogvault import *`
__all__ = [
    "Chatbot",
    "ChunkEvent",
    "Message",
    "Role",
    "SourcesEvent",
    "create_history",
    "Config",
    "ingest_files",
    "File",
    "load_uploaded_file",
]
