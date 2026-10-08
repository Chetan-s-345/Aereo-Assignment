import time


def wait_for_completion(client, job_id, timeout=5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        response = client.get(f"/api/v1/generation-jobs/{job_id}")
        assert response.status_code == 200
        data = response.json()
        if data["status"] == "completed":
            return data
        time.sleep(0.05)
    raise AssertionError("Job did not complete in time")


def test_create_generation_job(client):
    response = client.post("/api/v1/generation-jobs", json={
        "course_name": "Python Backend Engineering",
        "event_date": "2026-10-08",
        "recipients": [{"name": "Alice Johnson", "email": "alice@example.com"}, {"name": "Bob Smith"}],
    })
    assert response.status_code == 202
    body = response.json()
    assert body["total"] == 2
    assert body["status"] == "queued"


def test_input_validation(client):
    response = client.post("/api/v1/generation-jobs", json={
        "course_name": "X",
        "event_date": "not-a-date",
        "recipients": [{"name": "1", "email": "bad-email"}],
    })
    assert response.status_code == 422


def test_certificate_generation_and_retrieval(client):
    response = client.post("/api/v1/generation-jobs", json={
        "course_name": "FastAPI Workshop",
        "event_date": "2026-10-08",
        "recipients": [{"name": "Jane Doe", "email": "jane@example.com"}],
    })
    job = wait_for_completion(client, response.json()["job_id"])
    assert job["successful"] == 1
    assert job["failed"] == 0
    cert = job["certificates"][0]
    download = client.get(cert["download_url"])
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/pdf"
    assert download.content.startswith(b"%PDF")


def test_job_status_and_progress(client):
    response = client.post("/api/v1/generation-jobs", json={
        "course_name": "Testing",
        "event_date": "2026-10-08",
        "recipients": [{"name": "One Person"}, {"name": "Two Person"}],
    })
    job = wait_for_completion(client, response.json()["job_id"])
    assert job["progress_percent"] == 100.0
    assert job["successful"] == 2
    assert len(job["certificates"]) == 2


def test_individual_failure_does_not_stop_other_certificates(client):
    response = client.post("/api/v1/generation-jobs", json={
        "course_name": "Resilience Testing",
        "event_date": "2026-10-08",
        "recipients": [{"name": "Good Person"}, {"name": "[FAIL]"}, {"name": "Another Person"}],
    })
    job = wait_for_completion(client, response.json()["job_id"])
    assert job["successful"] == 2
    assert job["failed"] == 1
    failed = [c for c in job["certificates"] if c["status"] == "failed"][0]
    assert "Simulated certificate generation failure" in failed["error"]


def test_retrieve_job_certificates(client):
    response = client.post("/api/v1/generation-jobs", json={
        "course_name": "Certificate API",
        "event_date": "2026-10-08",
        "recipients": [{"name": "Recipient One"}],
    })
    job_id = response.json()["job_id"]
    wait_for_completion(client, job_id)
    response = client.get(f"/api/v1/generation-jobs/{job_id}/certificates")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_root_and_health_endpoints(client):
    root_res = client.get("/")
    assert root_res.status_code == 200
    assert root_res.json()["status"] == "online"

    health_res = client.get("/health")
    assert health_res.status_code == 200
    assert health_res.json()["status"] == "ok"


def test_list_generation_jobs_endpoint(client):
    # Create two jobs
    r1 = client.post("/api/v1/generation-jobs", json={
        "course_name": "Job One",
        "event_date": "2026-10-08",
        "recipients": [{"name": "Student A"}],
    })
    assert r1.status_code == 202
    wait_for_completion(client, r1.json()["job_id"])

    r2 = client.post("/api/v1/generation-jobs", json={
        "course_name": "Job Two",
        "event_date": "2026-10-08",
        "recipients": [{"name": "Student B"}],
    })
    assert r2.status_code == 202
    wait_for_completion(client, r2.json()["job_id"])

    # GET /api/v1/generation-jobs
    list_res = client.get("/api/v1/generation-jobs")
    assert list_res.status_code == 200
    jobs = list_res.json()
    assert len(jobs) >= 2
    assert any(j["job_id"] == r1.json()["job_id"] for j in jobs)
    assert any(j["job_id"] == r2.json()["job_id"] for j in jobs)


def test_route_aliases_without_api_v1(client):
    # POST /generation-jobs
    post_res = client.post("/generation-jobs", json={
        "course_name": "Alias Course",
        "event_date": "2026-10-08",
        "recipients": [{"name": "Alias Student"}],
    })
    assert post_res.status_code == 202
    job_id = post_res.json()["job_id"]

    # GET /generation-jobs
    list_res = client.get("/generation-jobs")
    assert list_res.status_code == 200

    # GET /generation-jobs/{job_id}
    job = wait_for_completion(client, job_id)
    assert job["successful"] == 1

    # GET /generation-jobs/{job_id}/certificates
    certs_res = client.get(f"/generation-jobs/{job_id}/certificates")
    assert certs_res.status_code == 200
    assert len(certs_res.json()) == 1


def test_empty_email_and_datetime_string_sanitization(client):
    response = client.post("/api/v1/generation-jobs", json={
        "course_name": "Sanitization Test",
        "event_date": "2026-10-08T15:30:00",
        "recipients": [
            {"name": "Empty Email Person", "email": ""},
            {"name": "Whitespace Email Person", "email": "   "},
        ],
    })
    assert response.status_code == 202
    job = wait_for_completion(client, response.json()["job_id"])
    assert job["successful"] == 2

