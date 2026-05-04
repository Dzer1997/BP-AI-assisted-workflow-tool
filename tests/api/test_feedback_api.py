#GET Feedback
def test_get_feedback_returns_list(client):
    response = client.get("/api/feedback")

    assert response.status_code == 200

    data = response.get_json()

    assert isinstance(data, list)
    
def test_get_feedback_empty(client):
    response = client.get("/api/feedback")

    assert response.status_code == 200

    data = response.get_json()

    assert isinstance(data, list)
    assert data == []


#POST Feedback
def test_create_feedback(client):
    payload = {
        "property_id": 123,
        "filename": "test.jpg",
        "score_type": "condition",
        "value": 5
    }

    response = client.post(
        "/api/feedback",
        json=payload
    )

    assert response.status_code == 201

    data = response.get_json()
    assert data["ok"] is True
    assert "id" in data

def test_create_feedback_missing_fields(client):
    payload = {
    }

    response = client.post(
        "/api/feedback",
        json=payload
    )

    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data

def test_create_feedback_missing_required_field(client):
    payload = {
        "property_id": 123
    }

    response = client.post(
        "/api/feedback",
        json=payload
    )

    assert response.status_code == 400

    data = response.get_json()
    assert "error" in data

def test_invalid_feedback_type(client):
    payload = {
        "property_id": 123,
        "filename": "test.jpg",
    }

    response = client.post(
        "/api/feedback",
        json=payload
    )

    assert response.status_code == 400

    data = response.get_json()
    assert "error" in data