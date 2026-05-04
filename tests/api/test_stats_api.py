def test_get_stats_returns_200(client):
    response = client.get("/api/stats")

    assert response.status_code == 200

    data = response.get_json()

    assert isinstance(data, dict)


def test_get_stats_structure(client):
    response = client.get("/api/stats")
    data = response.get_json()

    assert "correct" in data
    assert "fn" in data
    assert "fp" in data
    assert "precision" in data
    assert "recall" in data
    assert "total_classified" in data
    assert "calibration" in data

    calibration = data["calibration"]

    for key in ["condition", "modernity", "material", "functionality", "overall"]:
        assert key in calibration

        metric = calibration[key]

        assert "agreement_rate" in metric
        assert "bias" in metric
        assert "mae" in metric
        assert "pairs" in metric