from fastapi.testclient import TestClient

from app.main_bubblegrade import app

client = TestClient(app)

def test_upload_invalid_file():
    # Upload a non-image file should return 400
    response = client.post(
        "/api/v1/scans",
        files={"file": ("test.txt", b"abc", "text/plain")}
    )
    assert response.status_code == 400
    json_data = response.json()
    assert json_data.get("detail") == "Invalid file type. Only images are supported."