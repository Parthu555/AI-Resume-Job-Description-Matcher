import pytest
import numpy as np

def pytest_addoption(parser):
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run live pretrained model integration tests requiring internet/HuggingFace download"
    )

def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-integration"):
        skip_integration = pytest.mark.skip(reason="Pass --run-integration to run live pretrained model tests")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)

class MockSentenceTransformer:
    def __init__(self, *args, **kwargs):
        pass

    def encode(self, texts, show_progress_bar=False, normalize_embeddings=True, **kwargs):
        if isinstance(texts, str):
            texts = [texts]
        embeddings = []
        for text in texts:
            vec = np.zeros(384, dtype=np.float32)
            words = text.lower().split()
            if not words:
                vec[0] = 1.0
            else:
                for idx, word in enumerate(words):
                    slot = (abs(hash(word)) + idx) % 384
                    vec[slot] += 1.0
            norm = np.linalg.norm(vec)
            if norm == 0:
                vec[0] = 1.0
                norm = 1.0
            embeddings.append(vec / norm)
        return np.array(embeddings, dtype=np.float32)

@pytest.fixture(autouse=True)
def mock_embedding_model(monkeypatch, request):
    """
    Autouse fixture to mock SentenceTransformer in unit tests.
    Ensures unit tests run fast, reliably, and offline without requiring network downloads.
    """
    if "integration" in request.keywords:
        return None

    mock_model = MockSentenceTransformer()
    monkeypatch.setattr("backend.services.similarity_engine._CACHED_MODEL", mock_model)
    monkeypatch.setattr("backend.services.similarity_engine.get_embedding_model", lambda *args, **kwargs: mock_model)
    return mock_model
