"""Tests for the standalone ML analysis endpoint."""


def _post_text(payload: dict, client):
    return client.post("/api/v1/ml/analyze", json=payload)


def test_ml_analyze_returns_200_with_valid_text(client):
    response = _post_text(
        {
            "full_text": (
                "The results are consistent with prior work [1]. Our method "
                "was evaluated on a benchmark dataset [2]. The findings may "
                "suggest a relationship."
            ),
            "abstract": "The results are consistent with prior work.",
        },
        client,
    )

    assert response.status_code == 200
    body = response.json()
    assert "signals" in body
    assert "passed_rules" in body
    assert "ml_risk_contribution" in body
    assert "confidence" in body
    assert "summary" in body
    assert "features_used" in body


def test_ml_analyze_empty_text_returns_200_safe_result(client):
    response = _post_text({"full_text": ""}, client)

    assert response.status_code == 200
    body = response.json()
    assert body["confidence"] == 0.3
    assert isinstance(body["signals"], list)


def test_ml_analyze_missing_full_text_returns_422(client):
    response = _post_text({"abstract": "Only an abstract."}, client)

    assert response.status_code == 422


def test_ml_analyze_signals_never_none(client):
    response = _post_text({"full_text": "A short paper."}, client)

    assert response.status_code == 200
    assert response.json()["signals"] is not None


def test_ml_analyze_passed_rules_never_none(client):
    response = _post_text({"full_text": "A short paper."}, client)

    assert response.status_code == 200
    assert response.json()["passed_rules"] is not None


def test_ml_analyze_contribution_within_range(client):
    response = _post_text({"full_text": "A short paper."}, client)

    assert response.status_code == 200
    contribution = response.json()["ml_risk_contribution"]
    assert 0.0 <= contribution <= 100.0