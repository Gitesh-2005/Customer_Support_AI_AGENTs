async def test_login_issue():
    test_input = "i facing issue while logging in my account"
    response = await handle_ticket(test_input)
    print("Response:", json.dumps(response, indent=2))
    assert response["metadata"]["category"] == "login issue"
    assert "login" in response["summary"]["text"].lower()
    assert any("password" in action["description"].lower() or "login" in action["description"].lower() 
              for action in response["actions"])