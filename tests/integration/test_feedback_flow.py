import pytest
    
@pytest.mark.parametrize(
    "classification, expected_field",
    [
        ("correct", "correct"),
        ("fp", "fp"),
        ("fn", "fn"),
    ]
)
def test_feedback_updates_stats(client, classification, expected_field):
    
    before = client.get("/api/stats").get_json()

    response = client.post(
        "/api/feedback",
        json={
            "property_id": 123,
            "filename": "test.jpg",
            "classification": classification
        }
    )

    assert response.status_code == 201

    after = client.get("/api/stats").get_json()

    assert after[expected_field] > before[expected_field]

def test_feedback_flow(client):

    before = client.get("/api/stats").get_json()

    r1 = client.post(
        "/api/feedback",
        json={
            "property_id": 123,
            "filename": "test.jpg",
            "classification": "correct"
        }
    )

    assert r1.status_code == 201

    r2 = client.post(
        "/api/feedback",
        json={
            "property_id": 123,
            "filename": "test.jpg",
            "classification": "INVALID"
        }
    )

    assert r2.status_code == 400

    after = client.get("/api/stats").get_json()

    before_total = before["correct"] + before["fp"] + before["fn"]
    after_total = after["correct"] + after["fp"] + after["fn"]

    assert after_total > before_total