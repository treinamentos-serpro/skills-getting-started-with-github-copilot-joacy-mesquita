import importlib

import pytest
from fastapi.testclient import TestClient


app_module = importlib.import_module("src.app")


@pytest.fixture
def activity_data(monkeypatch):
    # Arrange: replace shared in-memory data with an isolated activity.
    activities = {
        "Chess Club": {
            "description": "Learn chess",
            "schedule": "Fridays",
            "max_participants": 3,
            "participants": ["student@example.com"],
        }
    }
    monkeypatch.setattr(app_module, "activities", activities)
    return activities


@pytest.fixture
def client(activity_data):
    return TestClient(app_module.app)


def test_get_activities_returns_activity_data(client, activity_data):
    # Arrange
    expected_activities = activity_data

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities


def test_signup_adds_participant(client, activity_data):
    # Arrange
    email = "new-student@example.com"

    # Act
    response = client.post("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert email in activity_data["Chess Club"]["participants"]


def test_signup_returns_404_for_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup", params={"email": "student@example.com"}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_duplicate_participant(client, activity_data):
    # Arrange
    email = "student@example.com"

    # Act
    response = client.post("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert activity_data["Chess Club"]["participants"] == [email]


def test_remove_signup_removes_participant(client, activity_data):
    # Arrange
    email = "student@example.com"

    # Act
    response = client.delete("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from Chess Club"}
    assert email not in activity_data["Chess Club"]["participants"]


def test_remove_signup_returns_404_for_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup", params={"email": "student@example.com"}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_signup_returns_404_for_unregistered_participant(client, activity_data):
    # Arrange
    email = "unregistered@example.com"

    # Act
    response = client.delete("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
    assert activity_data["Chess Club"]["participants"] == ["student@example.com"]