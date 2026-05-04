def test_stats_flow(client):
    before = client.get("/api/stats").get_json()

    assert before["correct"] == 0
    assert before["fp"] == 0
    assert before["fn"] == 0

    client.post(
        "/api/feedback",
        json={
            "property_id": 123,
            "filename": "test.jpg",
            "classification": "correct"
        }
    )

    after = client.get("/api/stats").get_json()

    assert after["correct"] == 1
    assert after["fp"] == 0
    assert after["fn"] == 0

    assert after["correct"] == before["correct"] + 1
    assert after["fp"] == before["fp"]
    assert after["fn"] == before["fn"]