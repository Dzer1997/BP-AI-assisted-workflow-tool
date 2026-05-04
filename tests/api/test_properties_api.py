def test_properties_empty(client):
    response = client.get("/api/properties")
    
    assert response.status_code == 200
    data = response.get_json()

    assert isinstance(data, list)

    assert data == []

