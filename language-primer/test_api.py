import pytest

def create_group(client, name="Test Group", member_names=None):
    if member_names is None:
        member_names = ["Alice", "Bob"]
    resp = client.post(
        "/api/groups",
        json={"groupName": name, "members": member_names},
    )
    return resp

def test_get_students_ok(client):
    create_group(client)
    res = client.get("/api/students")
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data, list) and len(data) >= 1
    seen_ids = set()
    for student in data:
        assert "id" in student and "name" in student
        assert isinstance(student["id"], int)
        assert isinstance(student["name"], str) and student["name"].strip()
        assert student["id"] not in seen_ids
        seen_ids.add(student["id"])

def testcreate_group_and_retrieve_members(client):
    create_resp = create_group(client, name="Group Alpha", member_names=["Alice", "Charlie"]) 
    assert create_resp.status_code == 201
    created = create_resp.get_json()
    assert {"id", "groupName", "members"} <= created.keys()
    group_id = created["id"]
    assert isinstance(group_id, int) and group_id > 0
    assert created["groupName"] == "Group Alpha"

    # Verify groups list includes the new group
    list_resp = client.get("/api/groups")
    assert list_resp.status_code == 200
    groups = list_resp.get_json()
    assert any(g.get("id") == group_id for g in groups)

    # Fetch single group and ensure member expansion to objects
    get_resp = client.get(f"/api/groups/{group_id}")
    assert get_resp.status_code == 200
    group = get_resp.get_json()
    assert group["id"] == group_id
    assert isinstance(group.get("members"), list)
    assert all(isinstance(m.get("id"), int) and isinstance(m.get("name"), str) for m in group["members"])

def test_add_member_to_group_and_prevent_duplicates(client):
    create_resp = create_group(client, name="Group Beta", member_names=["Alice"]) 
    assert create_resp.status_code == 201
    group_id = create_resp.get_json()["id"]

    res = client.get("/api/students")
    assert res.status_code == 200
    data = res.get_json()

    assert(len(data) > 0)

    # Add a valid new member by name, as per endpoint docstring
    add_resp = client.put(f"/api/groups/{group_id}/add", json={"studentId": data[0]['id']})
    assert add_resp.status_code in (200, 201)
    updated = add_resp.get_json()
    
    assert (data[0]['id'] in updated.get("members"))

    # Adding the same member again should be rejected with 400
    dup_resp = client.put(f"/api/groups/{group_id}/add", json={"studentId": data[0]['id']})
    assert dup_resp.status_code in (400, 409)

def test_delete_group_and_followup_404(client):
    create_resp = create_group(client, name="Group Gamma", member_names=["Alice"]) 
    assert create_resp.status_code == 201
    group_id = create_resp.get_json()["id"]

    del_resp = client.delete(f"/api/groups/{group_id}")
    assert del_resp.status_code in (200, 204)

    # Subsequent fetch should 404
    get_resp = client.get(f"/api/groups/{group_id}")
    assert get_resp.status_code == 404

    # Deleting again should 404
    del_again_resp = client.delete(f"/api/groups/{group_id}")
    assert del_again_resp.status_code == 404

def test_validation_and_edge_cases(client):
    # Invalid payloads
    for body in [
        {},
        {"groupName": ""},
        {"groupName": "No Members", "members": []},
    ]:
        resp = client.post("/api/groups", json=body)
        assert resp.status_code in (400, 422)

    # Non-existent group
    resp = client.get("/api/groups/999999")
    assert resp.status_code == 404

    # Add to non-existent group
    resp = client.put("/api/groups/999999/add", json={"studentId": 1})
    assert resp.status_code == 404

    # # Add invalid student
    create_resp = create_group(client, name="Group Delta", member_names=["Alice"]) 
    assert create_resp.status_code == 201
    group_id = create_resp.get_json()["id"]
    bad_add = client.put(f"/api/groups/{group_id}/add", json={"studentId": 999999})
    assert bad_add.status_code in (400, 404)


