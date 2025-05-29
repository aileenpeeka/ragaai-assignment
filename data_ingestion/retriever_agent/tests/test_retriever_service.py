import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
import numpy as np
from datetime import datetime
from ..retriever_service import app, Document, SearchQuery, SearchResult, get_redis_client, get_model, get_faiss_index
import json

client = TestClient(app)

@pytest.fixture(autouse=True)
def override_dependencies():
    # Mock Redis
    mock_redis = MagicMock()
    app.dependency_overrides[get_redis_client] = lambda: mock_redis
    # Mock model
    mock_model = MagicMock()
    mock_model.encode.return_value = np.array([0.1, 0.2, 0.3])
    mock_model.get_sentence_embedding_dimension.return_value = 3
    app.dependency_overrides[get_model] = lambda: mock_model
    # Mock FAISS index
    class MockFaissIndex:
        def __init__(self):
            self.embeddings = []
        def add(self, arr):
            self.embeddings.append(arr)
        def search(self, arr, k):
            # Return dummy scores and indices
            return np.array([[0.9, 0.8]]), np.array([[0, 1]])
    mock_faiss = MockFaissIndex()
    app.dependency_overrides[get_faiss_index] = lambda: mock_faiss
    yield
    app.dependency_overrides = {}

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()
    assert "timestamp" in response.json()

def test_add_document():
    """Test adding a document"""
    document = {
        "id": "test_doc_1",
        "content": "This is a test document",
        "metadata": {
            "source": "test",
            "date": datetime.now().isoformat()
        }
    }
    response = client.post("/documents", json=document)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == document["id"]
    assert data["content"] == document["content"]
    assert data["metadata"] == document["metadata"]
    assert "embedding" in data

def test_get_document():
    """Test getting a document"""
    document = {
        "id": "test_doc_1",
        "content": "This is a test document",
        "metadata": {
            "source": "test",
            "date": datetime.now().isoformat()
        },
        "embedding": [0.1, 0.2, 0.3]
    }
    # Set up the mock redis to return the document
    app.dependency_overrides[get_redis_client]().get.return_value = json.dumps(document)
    response = client.get("/documents/test_doc_1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == document["id"]
    assert data["content"] == document["content"]
    assert data["metadata"] == document["metadata"]
    assert data["embedding"] == document["embedding"]

def test_get_document_not_found():
    """Test getting a non-existent document"""
    app.dependency_overrides[get_redis_client]().get.return_value = None
    response = client.get("/documents/non_existent")
    assert response.status_code == 404

def test_search_documents():
    """Test searching documents"""
    doc1 = {
        "id": "test_doc_1",
        "content": "This is a test document about AI",
        "metadata": {"source": "test"},
        "embedding": [0.1, 0.2, 0.3]
    }
    doc2 = {
        "id": "test_doc_2",
        "content": "This is another test document about machine learning",
        "metadata": {"source": "test"},
        "embedding": [0.2, 0.3, 0.4]
    }
    client.post("/documents", json=doc1)
    client.post("/documents", json=doc2)
    # Set up the mock redis to return the correct documents for search
    redis_mock = app.dependency_overrides[get_redis_client]()
    redis_mock.get.side_effect = lambda key: (
        json.dumps(doc1) if key == "doc:0" else json.dumps(doc2) if key == "doc:1" else None
    )
    query = {
        "query": "artificial intelligence",
        "limit": 5,
        "min_score": 0.5
    }
    response = client.post("/search", json=query)
    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list)
    assert len(results) > 0
    assert all("document" in result and "score" in result for result in results)

def test_delete_document():
    """Test deleting a document"""
    document = {
        "id": "test_doc_1",
        "content": "This is a test document",
        "metadata": {"source": "test"},
        "embedding": [0.1, 0.2, 0.3]
    }
    client.post("/documents", json=document)
    response = client.delete("/documents/test_doc_1")
    assert response.status_code == 200
    assert response.json()["message"] == "Document deleted successfully"
    app.dependency_overrides[get_redis_client]().get.return_value = None
    response = client.get("/documents/test_doc_1")
    assert response.status_code == 404

def test_delete_document_not_found():
    """Test deleting a non-existent document"""
    # Set up the mock redis .exists() to return False
    app.dependency_overrides[get_redis_client]().exists.return_value = False
    response = client.delete("/documents/non_existent")
    assert response.status_code == 404

def test_document_model():
    """Test Document Pydantic model"""
    data = {
        "id": "test_doc_1",
        "content": "This is a test document",
        "metadata": {
            "source": "test",
            "date": datetime.now().isoformat()
        },
        "embedding": [0.1, 0.2, 0.3]
    }
    document = Document(**data)
    assert document.id == data["id"]
    assert document.content == data["content"]
    assert document.metadata == data["metadata"]
    assert document.embedding == data["embedding"]

def test_search_query_model():
    """Test SearchQuery Pydantic model"""
    data = {
        "query": "test query",
        "limit": 10,
        "min_score": 0.7
    }
    query = SearchQuery(**data)
    assert query.query == data["query"]
    assert query.limit == data["limit"]
    assert query.min_score == data["min_score"]

def test_search_result_model():
    """Test SearchResult Pydantic model"""
    document = Document(
        id="test_doc_1",
        content="This is a test document",
        metadata={"source": "test"},
        embedding=[0.1, 0.2, 0.3]
    )
    data = {
        "document": document,
        "score": 0.85
    }
    result = SearchResult(**data)
    assert result.document == document
    assert result.score == data["score"] 