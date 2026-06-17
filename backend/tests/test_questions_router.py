import pytest


class TestListQuestions:
    def test_returns_all_questions(self, client):
        resp = client.get("/questions")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 30

    def test_filter_by_difficulty_easy(self, client):
        resp = client.get("/questions?difficulty=easy")
        assert resp.status_code == 200
        results = resp.json()
        assert len(results) > 0
        assert all(q["difficulty"] == "easy" for q in results)

    def test_filter_by_difficulty_medium(self, client):
        resp = client.get("/questions?difficulty=medium")
        results = resp.json()
        assert all(q["difficulty"] == "medium" for q in results)

    def test_filter_by_difficulty_hard(self, client):
        resp = client.get("/questions?difficulty=hard")
        results = resp.json()
        assert len(results) == 5
        assert all(q["difficulty"] == "hard" for q in results)

    def test_filter_by_tag(self, client):
        resp = client.get("/questions?tag=hash-map")
        results = resp.json()
        assert len(results) > 0
        assert all("hash-map" in q["tags"] for q in results)

    def test_each_question_has_required_fields(self, client):
        resp = client.get("/questions")
        for q in resp.json():
            assert "id" in q
            assert "title" in q
            assert "difficulty" in q
            assert "hints" in q
            assert "follow_ups" in q
            assert "test_cases" in q

    def test_difficulty_counts_sum_to_total(self, client):
        easy = len(client.get("/questions?difficulty=easy").json())
        medium = len(client.get("/questions?difficulty=medium").json())
        hard = len(client.get("/questions?difficulty=hard").json())
        total = len(client.get("/questions").json())
        assert easy + medium + hard == total


class TestGetQuestion:
    def test_returns_known_question(self, client):
        resp = client.get("/questions/lc-1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "lc-1"
        assert data["title"] == "Two Sum"

    def test_404_for_unknown_id(self, client):
        resp = client.get("/questions/does-not-exist")
        assert resp.status_code == 404

    def test_returned_question_has_test_cases(self, client):
        resp = client.get("/questions/lc-1")
        data = resp.json()
        assert len(data["test_cases"]) > 0
        assert "input" in data["test_cases"][0]
        assert "output" in data["test_cases"][0]
