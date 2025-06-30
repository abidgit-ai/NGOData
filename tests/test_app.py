import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import app as app_module
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest

@pytest.fixture()
def client():
    # Set up in-memory database for testing
    test_engine = create_engine('sqlite:///:memory:')
    app_module.engine = test_engine
    app_module.Session = sessionmaker(bind=test_engine)
    app_module.Base.metadata.create_all(test_engine)
    app_module.metadata.create_all(test_engine)
    app_module.app.config['TESTING'] = True
    with app_module.app.test_client() as client:
        yield client

def test_index_lists_surveys(client):
    session = app_module.Session()
    survey = app_module.Survey(title="Example Survey", description="desc")
    session.add(survey)
    session.commit()

    response = client.get('/')
    assert response.status_code == 200
    assert b"Example Survey" in response.data
