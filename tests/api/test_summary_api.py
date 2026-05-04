def test_summary_structure(client):
    response = client.get("/api/summary")

    assert response.status_code == 200

    data = response.get_json()

    assert isinstance(data, dict)

    expected_keys = [
        "actionability_rate",
        "at_risk_properties",
        "confidence_metrics",
        "damage_frequency",
        "per_proposal_stats",
        "pipeline_funnel",
        "room_damage_profiles",
        "room_distribution",
        "room_grades",
        "severity_breakdown"
    ]

    for key in expected_keys:
        assert key in data

    actionability = data["actionability_rate"]

    assert isinstance(actionability, dict)

    assert "actionable_kb_images" in actionability
    assert "total_kb_images" in actionability
    assert "rate_percent" in actionability

    assert isinstance(actionability["rate_percent"], (int, float))

