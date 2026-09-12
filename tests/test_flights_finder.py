from unittest.mock import patch, MagicMock
import requests
from agents.tools.flights_finder import flights_finder


def test_round_trip_uses_roundtrip_endpoint():
    fake = MagicMock(status_code=200)
    fake.json.return_value = {"success": True, "results": []}
    with patch("agents.tools.flights_finder.requests.get", return_value=fake) as mock_get:
        result = flights_finder(origin="JFK", destination="LHR", date="2026-09-01", return_date="2026-09-08")
    assert result == {"success": True, "results": []}
    assert "roundtrip" in mock_get.call_args[0][0]


def test_one_way_uses_search_endpoint():
    fake = MagicMock(status_code=200)
    fake.json.return_value = {"success": True, "results": []}
    with patch("agents.tools.flights_finder.requests.get", return_value=fake) as mock_get:
        flights_finder(origin="JFK", destination="LHR", date="2026-09-01")
    called_url = mock_get.call_args[0][0]
    assert "search" in called_url and "roundtrip" not in called_url


def test_non_200_returns_error_dict():
    fake = MagicMock(status_code=403, text="Forbidden")
    with patch("agents.tools.flights_finder.requests.get", return_value=fake):
        result = flights_finder(origin="JFK", destination="LHR", date="2026-09-01")
    assert "error" in result and "403" in result["error"]


def test_network_error_returns_error_dict():
    with patch("agents.tools.flights_finder.requests.get", side_effect=requests.exceptions.Timeout("timed out")):
        result = flights_finder(origin="JFK", destination="LHR", date="2026-09-01")
    assert "error" in result and "Network error" in result["error"]