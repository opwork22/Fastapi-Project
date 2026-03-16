from fastapi.testclient import TestClient
import base64


def basic_auth(username: str, password: str):
    token = f"{username}:{password}"
    encoded = base64.b64encode(token.encode()).decode()
    return {"Authorization": f"Basic {encoded}"}


def test_register_user(client: TestClient):
    payload = {
        "username": "newuser",
        "password": "Password@123"
    }

    response = client.post("/register", json=payload)

    assert response.status_code == 200
    assert response.json()["message"] == "User registered successfully"


def test_get_notes_empty(client: TestClient, test_user):
    headers = basic_auth("testuser", "Password@123")

    response = client.get("/notes", headers=headers)

    assert response.status_code == 200
    assert response.json() == {"notes": []}


def test_add_note(client: TestClient, test_user):
    headers = basic_auth("testuser", "Password@123")

    response = client.post(
        "/notes/add",
        json={"note": "My first test note"},
        headers=headers
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Note added successfully"


def test_get_notes_after_add(client: TestClient, test_user):
    headers = basic_auth("testuser", "Password@123")

    client.post(
        "/notes/add",
        json={"note": "Note 1"},
        headers=headers
    )

    response = client.get(
        "/notes",
        headers=headers
    )

    assert response.status_code == 200
    assert len(response.json()["notes"]) == 1


def test_update_note(client: TestClient, test_user):
    headers = basic_auth("testuser", "Password@123")

    client.post(
        "/notes/add",
        json={"note": "Old Note"},
        headers=headers
    )

    response = client.put(
        "/update/note",
        json={
            "note_index": 0,
            "note": "Updated Note"
        },
        headers=headers
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Note updated successfully"


def test_update_password(client: TestClient, test_user):
    headers = basic_auth("testuser", "Password@123")

    response = client.put(
        "/update/password",
        json={
            "old_password": "Password@123",
            "new_password": "NewPassword@123"
        },
        headers=headers
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Password updated successfully"

def test_delete_note(client: TestClient, test_user):
    headers = basic_auth("testuser", "Password@123")

    client.post(
        "/notes/add",
        json={"note": "Delete Me"},
        headers=headers
    )

    response = client.request(
        "DELETE",
        "/delete",
        json={
            "delete_type": "notes",
            "note_index": 0
        },
        headers=headers
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Deleted successfully"

def test_delete_user(client: TestClient, test_user):
    headers = basic_auth("testuser", "Password@123")

    response = client.request(
        "DELETE",
        "/delete",
        json={
            "delete_type": "user"
        },
        headers=headers
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Deleted successfully"