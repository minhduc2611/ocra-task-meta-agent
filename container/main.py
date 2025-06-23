from __init__ import app
import logging
from libs.weaviate_lib import initialize_schema, close_client
from contextlib import contextmanager
import os
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@contextmanager
def weaviate_connection():
    try:
        yield
    finally:
        close_client()

if __name__ == '__main__':
    with weaviate_connection():
        initialize_schema()
        port = int(os.environ.get("PORT", 8080))
        app.run(host="0.0.0.0", port=port, threaded=False)
