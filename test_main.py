"""Module to test the FastAPI app in main.py"""
import requests

import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture
def test_client():
    """Create a FastAPI test client"""
    return TestClient(main.app)


def test_get_member_data_with_retry(monkeypatch):
    """Test get_member_data function with retry logic"""
    # Define a sample response from the external API
    sample_data = {
        'oop_max': 10000,
        'remaining_oop_max': 9000,
        'copay': 1000
    }

    # Define a mock function for the requests.get method with retries
    def mock_get(
        url, # pylint: disable=unused-argument
        params, # pylint: disable=unused-argument
        timeout # pylint: disable=unused-argument
    ):
        class MockResponse(requests.models.Response):
            """ A class to mock ome sample data for all requests """
            def __init__(self, json_data, status_code):
                super().__init__()
                self.json_data = json_data
                self.status_code = status_code

            def json(self, **kwargs):
                return self.json_data
        if url == 'http://test.com' or mock_get.call_count > 3:
            return MockResponse(sample_data, 200)

        mock_get.call_count += 1
        raise requests.exceptions.RequestException("Mock error")

    mock_get.call_count = 0

    monkeypatch.setattr(main.requests, 'get', mock_get)

    # Test a non-working call to a URL
    member_data = main.get_member_data('http://example.com', 123)
    assert member_data is None

    # Test a call to a URL that is non-working at first, but works after a few retries'
    mock_get.call_count = 0
    member_data = main.get_member_data('http://example.com', 123, 5)
    assert member_data == sample_data

    # Test a call to a working (mocked) URL
    mock_get.call_count = 0
    member_data = main.get_member_data('http://test.com', 123)
    assert member_data == sample_data

def test_get_formatted_mode():
    """Test get_formatted_mode function"""
    # Test with a list containing multiple occurrences of the same value
    data_list = [1000, 2000, 1000, 1000, 3000]
    assert main.get_formatted_mode(data_list) == '$10.00'

    # Test with a list containing unique values
    data_list = [1500, 2500, 1800, 3000]
    assert main.get_formatted_mode(data_list) == '$15.00'

    # Test with an empty list
    data_list = []
    assert main.get_formatted_mode(data_list) is None

def test_root_endpoint(
        monkeypatch,
        test_client # pylint: disable=redefined-outer-name
):
    """Test the root endpoint"""
    # Define sample responses from the external APIs
    sample_data_1 = {
        'oop_max': 10000,
        'remaining_oop_max': 9000,
        'copay': 1000
    }

    sample_data_2 = {
        'oop_max': 20000,
        'remaining_oop_max': 9000,
        'copay': 5000
    }

    sample_data_3 = {
        'oop_max': 10000,
        'remaining_oop_max': 8000,
        'copay': 1000
    }

    # Mock the requests.get function to return sample data
    def mock_get(
            url,
            params, # pylint: disable=unused-argument
            timeout # pylint: disable=unused-argument
    ):
        class MockResponse(requests.models.Response):
            """ A class to mock request reponses """
            def __init__(self, json_data, status_code):
                super().__init__()
                self.json_data = json_data
                self.status_code = status_code

            def json(self, **kwargs):
                return self.json_data

        if 'api1' in url:
            return MockResponse(sample_data_1, 200)
        if 'api2' in url:
            return MockResponse(sample_data_2, 200)
        if 'api3' in url:
            return MockResponse(sample_data_3, 200)
        # Return a simple mock response for unknown URLs
        return MockResponse({}, 404)


    monkeypatch.setattr(main.requests, 'get', mock_get)

    # Test the root endpoint with a member ID
    response = test_client.get('/123')

    # Assert that the response status code is 200
    assert response.status_code == 200

    # Assert that the response contains the expected data
    expected_data = {
        'oop_max': '$100.00',
        'remaining_oop_max': '$90.00',
        'copay': '$10.00'
    }
    assert response.json() == expected_data
