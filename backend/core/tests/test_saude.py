def test_endpoint_saude(client):
    resposta = client.get("/saude/")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}
