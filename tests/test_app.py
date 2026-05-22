"""Integration tests for Mergington High School API"""

import pytest


class TestRootEndpoint:
    """Tests for GET / endpoint"""

    def test_root_redirect(self, client):
        """Test that root endpoint redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code in [307, 308]
        assert "/static/index.html" in response.headers["location"]


class TestActivitiesEndpoint:
    """Tests for GET /activities endpoint"""

    def test_get_all_activities(self, client):
        """Test retrieving all available activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        
        # Verify all 9 activities are present
        assert len(activities) == 9
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Track and Field",
            "Visual Arts",
            "Music Ensemble",
            "Debate Club",
            "Science Club"
        ]
        assert set(activities.keys()) == set(expected_activities)

    def test_activity_structure(self, client):
        """Test that each activity has correct structure"""
        response = client.get("/activities")
        activities = response.json()
        
        # Verify each activity has required fields
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_data, dict)
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            
            # Verify data types
            assert isinstance(activity_data["description"], str)
            assert isinstance(activity_data["schedule"], str)
            assert isinstance(activity_data["max_participants"], int)
            assert isinstance(activity_data["participants"], list)

    def test_initial_participants_count(self, client):
        """Test that initial participants are present"""
        response = client.get("/activities")
        activities = response.json()
        
        # Chess Club should have 2 initial participants
        assert len(activities["Chess Club"]["participants"]) == 2
        assert "michael@mergington.edu" in activities["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in activities["Chess Club"]["participants"]


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_successful_signup(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]

    def test_signup_persists(self, client):
        """Test that signup persists in the activities list"""
        # First signup
        client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        # Verify signup persisted
        response = client.get("/activities")
        activities = response.json()
        assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]

    def test_duplicate_signup_fails(self, client):
        """Test that duplicate signup returns 400 error"""
        # Student already in Chess Club
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()

    def test_signup_nonexistent_activity(self, client):
        """Test signup for non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_multiple_students_can_signup(self, client):
        """Test that multiple different students can sign up for same activity"""
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"
        
        response1 = client.post(
            "/activities/Programming Class/signup",
            params={"email": email1}
        )
        response2 = client.post(
            "/activities/Programming Class/signup",
            params={"email": email2}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify both are in the activity
        response = client.get("/activities")
        participants = response.json()["Programming Class"]["participants"]
        assert email1 in participants
        assert email2 in participants

    def test_signup_with_special_characters_in_email(self, client):
        """Test signup with email containing special characters"""
        response = client.post(
            "/activities/Visual Arts/signup",
            params={"email": "student+test@mergington.edu"}
        )
        assert response.status_code == 200

    def test_student_can_signup_for_multiple_activities(self, client):
        """Test that same student can sign up for different activities"""
        email = "versatile@mergington.edu"
        
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        response2 = client.post(
            "/activities/Music Ensemble/signup",
            params={"email": email}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify in both activities
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Music Ensemble"]["participants"]


class TestRemoveParticipantEndpoint:
    """Tests for DELETE /activities/{activity_name}/participants endpoint"""

    def test_successful_removal(self, client):
        """Test successful removal of participant from activity"""
        response = client.delete(
            "/activities/Chess Club/participants",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Removed" in data["message"]

    def test_removal_persists(self, client):
        """Test that removal persists in the activities list"""
        # Remove participant
        client.delete(
            "/activities/Chess Club/participants",
            params={"email": "michael@mergington.edu"}
        )
        
        # Verify removal persisted
        response = client.get("/activities")
        activities = response.json()
        assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]

    def test_remove_nonexistent_participant(self, client):
        """Test removing participant not in activity returns 404"""
        response = client.delete(
            "/activities/Chess Club/participants",
            params={"email": "notareal@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_remove_from_nonexistent_activity(self, client):
        """Test removing from non-existent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent Activity/participants",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_remove_then_readd(self, client):
        """Test that participant can be re-added after removal"""
        email = "michael@mergington.edu"
        
        # Remove
        response_remove = client.delete(
            "/activities/Chess Club/participants",
            params={"email": email}
        )
        assert response_remove.status_code == 200
        
        # Re-add
        response_signup = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response_signup.status_code == 200
        
        # Verify re-added
        response = client.get("/activities")
        assert email in response.json()["Chess Club"]["participants"]


class TestDatabaseIsolation:
    """Tests to verify test isolation and database state management"""

    def test_signup_does_not_leak_between_tests(self, client):
        """Test that signups from one test don't affect another"""
        # This test verifies fixture works by checking initial state
        response = client.get("/activities")
        chess_club = response.json()["Chess Club"]
        
        # Should have only initial 2 participants
        assert len(chess_club["participants"]) == 2

    def test_removal_does_not_leak_between_tests(self, client):
        """Test that removals from one test don't affect another"""
        # This test verifies fixture works by checking initial state
        response = client.get("/activities")
        chess_club = response.json()["Chess Club"]
        
        # Both original participants should still be present
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]
