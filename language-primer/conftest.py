import os
import sys
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


@pytest.fixture(scope="session")
def app():
    from server.server import app as flask_app

    flask_app.testing = True
    yield flask_app


@pytest.fixture()
def client(app):
    return app.test_client()


