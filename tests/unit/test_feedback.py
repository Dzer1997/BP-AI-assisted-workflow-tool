def test_post_feedback_validation(client):
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
            "filename": "test.txt",
            "classification": "INVALID"
        }
    )

    assert r2.status_code == 400
