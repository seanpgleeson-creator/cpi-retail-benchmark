"""
Basic tests to verify the test setup is working
"""

import pytest
from app import __version__


def test_version():
    """Test that version is defined"""
    assert __version__ == "0.1.0"


def test_basic_math():
    """Basic test to verify pytest is working"""
    assert 1 + 1 == 2


@pytest.mark.unit
def test_unit_marker():
    """Test the unit marker"""
    assert True


@pytest.mark.integration
def test_integration_marker():
    """Test the integration marker"""
    assert True
