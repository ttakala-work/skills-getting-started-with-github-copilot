from src.app import activities

NEW_EMAIL = "newstudent@mergington.edu"


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_all_activities(client):
    response = client.get("/activities")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == len(activities)
    assert "Chess Club" in data
    for details in data.values():
        assert {"description", "schedule", "max_participants", "participants"} <= details.keys()


def test_signup_adds_participant(client):
    response = client.post("/activities/Chess Club/signup", params={"email": NEW_EMAIL})

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {NEW_EMAIL} for Chess Club"}
    assert NEW_EMAIL in client.get("/activities").json()["Chess Club"]["participants"]


def test_signup_unknown_activity_returns_404(client):
    response = client.post("/activities/Unknown/signup", params={"email": NEW_EMAIL})

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_duplicate_returns_400(client):
    existing = activities["Chess Club"]["participants"][0]

    response = client.post("/activities/Chess Club/signup", params={"email": existing})

    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up"
    assert activities["Chess Club"]["participants"].count(existing) == 1


def test_unregister_removes_participant(client):
    existing = activities["Chess Club"]["participants"][0]

    response = client.delete("/activities/Chess Club/signup", params={"email": existing})

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {existing} from Chess Club"}
    assert existing not in client.get("/activities").json()["Chess Club"]["participants"]


def test_unregister_unknown_activity_returns_404(client):
    response = client.delete("/activities/Unknown/signup", params={"email": NEW_EMAIL})

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_not_signed_up_returns_404(client):
    response = client.delete("/activities/Chess Club/signup", params={"email": NEW_EMAIL})

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_signup_then_unregister_round_trip(client):
    before = list(activities["Art Studio"]["participants"])

    assert client.post("/activities/Art Studio/signup", params={"email": NEW_EMAIL}).status_code == 200
    assert client.delete("/activities/Art Studio/signup", params={"email": NEW_EMAIL}).status_code == 200

    assert client.get("/activities").json()["Art Studio"]["participants"] == before


def test_state_is_isolated_between_tests(client):
    # Earlier tests mutate Chess Club; the reset fixture must restore the seed data.
    assert activities["Chess Club"]["participants"] == ["michael@mergington.edu", "daniel@mergington.edu"]
