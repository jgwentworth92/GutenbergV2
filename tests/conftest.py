import os
import pytest




@pytest.fixture
def the_name():
    return os.environ.get('GITHUB_TOKEN')