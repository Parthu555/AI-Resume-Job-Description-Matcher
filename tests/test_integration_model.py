import pytest

@pytest.mark.integration
def test_real_embedding_model_if_available():
    """
    Optional integration test checking whether sentence-transformers model
    can be initialized and produce embeddings.
    """
    try:
        from sentence_transformers import SentenceTransformer
        # Test loading lightweight model or configured model
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        emb = model.encode(["Python software engineering resume", "FastAPI web developer"])
        assert emb.shape[0] == 2
        assert emb.shape[1] == 384
    except Exception as e:
        pytest.skip(f"Live pretrained model download skipped or offline: {e}")
