# tests/test_app.py

import unittest
import json
from werkzeug.security import generate_password_hash # For creating test user passwords
from app import app, db  # Assuming your main Flask app instance is 'app' and db instance is 'db'
from models import User, Friend, DetailedAnalysis, GameModeStats # Import your models

class BaseTestCase(unittest.TestCase):
    """A base test case."""

    def setUp(self):
        # -- App Configuration for Testing --
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False # Disable CSRF for testing forms if you use Flask-WTF
        app.config['DEBUG'] = False
        # Use an in-memory SQLite database for testing
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client() # Creates a test client for making requests

        # -- Database Setup --
        with app.app_context():
            db.create_all() # Create all database tables

        # -- Optional: Create some initial data or users --
        self.create_test_users()

    def tearDown(self):
        # -- Database Teardown --
        with app.app_context():
            db.session.remove() # Clear the session
            db.drop_all() # Drop all database tables

    def create_test_users(self):
        # Helper method to create some test users
        with app.app_context():
            user1 = User(
                username='testuser1',
                email='test1@example.com',
                password=generate_password_hash('password123')
            )
            user2 = User(
                username='testuser2',
                email='test2@example.com',
                password=generate_password_hash('password456')
            )
            db.session.add_all([user1, user2])
            db.session.commit()

    def register_user(self, username, email, password, riot_id="", tagline="", region=""):
        # Helper to register a user via API or form post
        # Assuming you have a /register route that accepts POST requests
        return self.app.post(
            '/register',
            data=dict(
                username=username,
                email=email,
                password=password,
                confirm_password=password, # If your form has confirm_password
                riot_id=riot_id,
                tagline=tagline,
                region=region
            ),
            follow_redirects=True
        )

    def login_user(self, username, password):
        # Helper to log in a user
        return self.app.post(
            '/login',
            data=dict(username=username, password=password),
            follow_redirects=True
        )

    def logout_user(self):
        # Helper to log out a user
        return self.app.get('/logout', follow_redirects=True)


class AuthTests(BaseTestCase):
    """Test authentication functionalities."""

    def test_registration_page_loads(self):
        # Test if the registration page loads correctly
        response = self.app.get('/register')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Sign Up', response.data) # Check for some text on the page

    def test_user_registration(self):
        # Test user registration process
        response = self.register_user('newuser', 'new@example.com', 'newpassword')
        self.assertEqual(response.status_code, 200) # Should redirect to login or dashboard
        # Check if redirected to login after successful registration (depends on your app logic)
        self.assertIn(b'Sign up succeed! Now login...', response.data) # Flash message

        with app.app_context():
            user = User.query.filter_by(username='newuser').first()
            self.assertIsNotNone(user)
            self.assertEqual(user.email, 'new@example.com')

    def test_login_page_loads(self):
        # Test if the login page loads correctly
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Sign In', response.data) # Check for some text

    def test_user_login_logout(self):
        # Test user login and logout
        self.register_user('loginuser', 'login@example.com', 'loginpass') # First register
        login_response = self.login_user('loginuser', 'loginpass')
        self.assertEqual(login_response.status_code, 200)
        self.assertIn(b'Login success', login_response.data) # Flash message or text on dashboard
        # Check if session is set
        with self.app as client:
            client.post('/login', data=dict(username='loginuser', password='loginpass'))
            with client.session_transaction() as sess:
                self.assertTrue(sess.get('user_id') is not None)

        logout_response = self.logout_user()
        self.assertEqual(logout_response.status_code, 200)
        self.assertIn(b'Log out!', logout_response.data) # Flash message
        with self.app as client:
            client.get('/logout') # Ensure session is cleared
            with client.session_transaction() as sess:
                self.assertIsNone(sess.get('user_id'))

    def test_login_with_invalid_credentials(self):
        # Test login with wrong password
        self.register_user('creduser', 'cred@example.com', 'correctpass')
        response = self.login_user('creduser', 'wrongpass')
        self.assertEqual(response.status_code, 200) # Stays on login page
        self.assertIn(b'Username or password not correct', response.data) # Flash message

class FriendAPITests(BaseTestCase):
    """Test Friend related API endpoints."""

    def setUp(self):
        super().setUp()
        # Register and log in users for friend tests
        self.user1_id = User.query.filter_by(username='testuser1').first().id
        self.user2_id = User.query.filter_by(username='testuser2').first().id

    def test_search_user_api_requires_login(self):
        # Test that search user API requires login
        response = self.app.get('/api/search_user?query=test')
        self.assertEqual(response.status_code, 302) # Redirects to login

    def test_search_user_api(self):
        # Test searching for a user
        self.login_user('testuser1', 'password123')
        response = self.app.get('/api/search_user?query=testuser2')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertTrue(len(data['data']) > 0)
        self.assertEqual(data['data'][0]['username'], 'testuser2')
        self.logout_user()

    def test_add_friend_api(self):
        # Test adding a friend
        self.login_user('testuser1', 'password123')
        response = self.app.post(
            '/api/add_friend',
            data=json.dumps(dict(friend_id=self.user2_id)),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn(f"已添加 testuser2 为好友", data['message']) # "Added testuser2 as friend"

        # Verify friend relationship in DB (both ways)
        with app.app_context():
            f1 = Friend.query.filter_by(user_id=self.user1_id, friend_id=self.user2_id).first()
            f2 = Friend.query.filter_by(user_id=self.user2_id, friend_id=self.user1_id).first()
            self.assertIsNotNone(f1)
            self.assertIsNotNone(f2)
        self.logout_user()

    def test_get_friends_api(self):
        # Test getting the friends list
        # First, add a friend
        self.login_user('testuser1', 'password123')
        self.app.post(
            '/api/add_friend',
            data=json.dumps(dict(friend_id=self.user2_id)),
            content_type='application/json'
        )
        # Now get friends
        response = self.app.get('/api/friends')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(len(data['data']), 1)
        self.assertEqual(data['data'][0]['username'], 'testuser2')
        self.logout_user()

    def test_remove_friend_api(self):
        # Test removing a friend
        self.login_user('testuser1', 'password123')
        # Add friend first
        self.app.post(
            '/api/add_friend',
            data=json.dumps(dict(friend_id=self.user2_id)),
            content_type='application/json'
        )
        # Then remove
        response = self.app.post(
            '/api/remove_friend',
            data=json.dumps(dict(friend_id=self.user2_id)),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn(f"已从好友列表中移除 testuser2", data['message']) # "Removed testuser2 from friends list"

        # Verify friend relationship is removed from DB
        with app.app_context():
            f1 = Friend.query.filter_by(user_id=self.user1_id, friend_id=self.user2_id).first()
            self.assertIsNone(f1)
        self.logout_user()

class ShareAPITests(BaseTestCase):
    """Test Share page related API endpoint."""

    def setUp(self):
        super().setUp()
        self.user1_id = User.query.filter_by(username='testuser1').first().id
        self.user2_id = User.query.filter_by(username='testuser2').first().id

        # Make user1 and user2 friends
        with app.app_context():
            db.session.add(Friend(user_id=self.user1_id, friend_id=self.user2_id))
            db.session.add(Friend(user_id=self.user2_id, friend_id=self.user1_id)) # Bidirectional
            db.session.commit()

    def test_get_friend_summary_api_no_data(self):
        # Test getting friend summary when friend has no analysis data
        self.login_user('testuser1', 'password123')
        response = self.app.get(f'/api/friend_summary/{self.user2_id}')
        self.assertEqual(response.status_code, 200) # As per your API, 200 with "info"
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'info')
        self.assertIn("Analysis data for testuser2 is not available yet", data['message'])
        self.assertEqual(data['data']['username'], 'testuser2')
        self.assertEqual(data['data']['total_multikills'], 0)
        self.logout_user()

    def test_get_friend_summary_api_with_data(self):
        # Test getting friend summary when friend HAS analysis data
        # First, create some dummy analysis data for user2
        with app.app_context():
            detailed = DetailedAnalysis(
                user_id=self.user2_id,
                favorite_champions={'Ashe': 5, 'Lux': 3, 'Garen': 2, 'Yasuo': 1},
                double_kills=10,
                triple_kills=5,
                quadra_kills=2,
                penta_kills=1
            )
            modes = GameModeStats(
                user_id=self.user2_id,
                sr_5v5_percentage=60.0,
                aram_percentage=30.0,
                fun_modes_percentage=10.0,
                total_matches=20
            )
            db.session.add_all([detailed, modes])
            db.session.commit()

        self.login_user('testuser1', 'password123')
        response = self.app.get(f'/api/friend_summary/{self.user2_id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['data']['username'], 'testuser2')
        self.assertListEqual(data['data']['favorite_champions'], ['Ashe', 'Lux', 'Garen']) # Top 3
        self.assertEqual(data['data']['total_multikills'], 18) # 10+5+2+1
        self.assertEqual(data['data']['favorite_game_mode'], "Summoner's Rift 5v5")
        self.logout_user()

    def test_get_friend_summary_not_a_friend(self):
        # Test accessing summary of a user who is not a friend
        # Create a third user who is not a friend of user1
        with app.app_context():
            user3 = User(username='testuser3', email='test3@example.com', password=generate_password_hash('pass789'))
            db.session.add(user3)
            db.session.commit()
            user3_id = user3.id

        self.login_user('testuser1', 'password123')
        response = self.app.get(f'/api/friend_summary/{user3_id}')
        self.assertEqual(response.status_code, 403) # Forbidden or error
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
        self.assertIn("Requested user is not a friend or permission denied", data['message'])
        self.logout_user()


if __name__ == '__main__':
    unittest.main()