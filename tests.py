import tempfile
import unittest

import mock as mock
from werkzeug.exceptions import NotFound
from wtforms import ValidationError

import auth
from app import app
from forms import LoginForm, username_exists, email_exists
from models import User, Todo
from resources.todos import todo_or_404, TodoList, Todo as TodoResource


class BasicTests(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

    def test_main_page(self):
        response = self.app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_login_page_loads(self):
        resp = self.app.get('/login', content_type='html/text')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Login', resp.data)

    def tearDown(self):
        pass


class UserModelTests(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.user = User.create_user(
            username='test',
            email='test@example.com',
            password='password',
            verify_password='password'
        )
        self.token = self.user.generate_auth_token()

    def test_create_user(self):
        user = User.create_user(
            username='test2',
            email='test2@example.com',
            password='password',
            verify_password='password'
        )
        self.assertEqual(user.username, 'test2')
        user.delete_instance()

    def test_create_user_exists(self):
        with self.assertRaises(Exception):
            User.create_user(
                username='test',
                email='test@example.com',
                password='password',
                verify_password='password'
            )

    def test_verify_auth_token(self):
        user = self.user.verify_auth_token(self.token)
        self.assertEqual(user.username, 'test')

    def test_verify_auth_token_fails(self):
        self.assertIsNone(User.verify_auth_token(''))

    def test_verify_password(self):
        result = self.user.verify_password('password')
        self.assertTrue(result)

    def tearDown(self):
        self.user.delete_instance()


class AuthTests(unittest.TestCase):

    def setUp(self):
        self.app = app.app_context()
        self.user = User.create_user(
            username='test3',
            email='test3@example.com',
            password='password',
            verify_password='password'
        )
        self.token = self.user.generate_auth_token()

    def test_verify_password_with_g_user(self):
        with self.app:
            self.app.g.user = self.user
            result = auth.verify_password('test3', 'password')
            self.assertTrue(result)

    def test_verify_password_no_user(self):
        with self.app:
            self.app.g.user = None
            result = auth.verify_password('fake', 'password')
            self.assertFalse(result)

    def test_verify_password_correct(self):
        with self.app:
            self.app.g.user = None
            result = auth.verify_password('test3', 'password')
            self.assertTrue(result)

    def test_verify_auth_token_valid(self):
        with self.app:
            result = auth.verify_token(self.token)
            self.assertTrue(result)

    def test_verify_auth_token_invalid(self):
        with self.app:
            result = auth.verify_token('')
            self.assertFalse(result)

    def tearDown(self):
        self.user.delete_instance()


class UserResourceTests(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = False
        self.db, app.config['DATABASE'] = tempfile.mkstemp()
        self.app = app.test_client()
        self.user = {
            'username': 'resource',
            'email': 'test@example.com',
            'password': 'password',
            'verify_password': 'password'
        }
        self.bad_user = {
            'username': 'resource',
            'email': 'test@example.com',
            'password': 'password',
            'verify_password': 'bad_pass'
        }

    def test_create_user_resource(self):
        with self.app:
            result = self.app.post('/api/v1/users', data=self.user)
            self.assertEqual(result.status_code, 201)
            user = User.get(username='resource')
            user.delete_instance()

    def test_bad_create_user_resource(self):
        with self.app:
            result = self.app.post('/api/v1/users', data=self.bad_user)
            self.assertEqual(result.status_code, 400)


class TodoResourceTests(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = False
        self.db, app.config['DATABASE'] = tempfile.mkstemp()
        self.user = User.create_user(
            username='testtodo',
            email='testtodo@example.com',
            password='password',
            verify_password='password'
        )
        Todo.create(
            name='TODO',
            created_by=self.user
        )
        self.todo = Todo.get(name='TODO')

    def test_todo_or_404_success(self):
        todo = todo_or_404(self.todo.id)
        self.assertEqual(todo, self.todo)

    def test_todo_or_404_fail(self):
        with self.assertRaises(NotFound):
            todo_or_404(333)

    def test_todolist_init(self):
        resource = TodoList()
        self.assertIsInstance(resource, TodoList)

    def test_todo_init(self):
        resource = TodoResource()
        self.assertIsInstance(resource, TodoResource)

    def tearDown(self):
        self.user.delete_instance()
        self.todo.delete_instance()


class FormTests(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.user = User.create_user(
            username='testform',
            email='testform@example.com',
            password='password',
            verify_password='password'
        )

    @mock.patch('flask_wtf.FlaskForm.__init__')
    def test_username_exists(self, fake_init):
        fake_init.return_value = None
        form = LoginForm()
        form.username.data = 'testform'
        with self.app:
            with self.assertRaises(ValidationError):
                username_exists(form, form.username)

    @mock.patch('flask_wtf.FlaskForm.__init__')
    def test_email_exists(self, fake_init):
        fake_init.return_value = None
        form = LoginForm()
        form.email.data = 'testform@example.com'
        with self.app:
            with self.assertRaises(ValidationError):
                email_exists(form, form.email)

    def tearDown(self):
        self.user.delete_instance()


if __name__ == "__main__":
    unittest.main()
