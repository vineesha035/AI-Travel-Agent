from unittest.mock import patch, MagicMock
import requests
from agents.tools.hotel_finder import hotels_finder, _resolve_destination


def test_resolve_destination_success():
    fake = MagicMock(status_code=200)
    fake.json.return_value = {"data": [{"dest_id": "-1456928", "search_type": "city"}]}
    with patch("agents.tools.hotel_finder.requests.get", return_value=fake):
        dest_id, search_type, error = _resolve_destination("Paris")
    assert dest_id == "-1456928" and search_type == "city" and error is None


def test_resolve_destination_no_matches():
    fake = MagicMock(status_code=200)
    fake.json.return_value = {"data": []}
    with patch("agents.tools.hotel_finder.requests.get", return_value=fake):
        dest_id, search_type, error = _resolve_destination("asdkfjasdf")
    assert dest_id is None and "No destination found" in error


def test_hotels_finder_propagates_resolve_error():
    with patch("agents.tools.hotel_finder._resolve_destination", return_value=(None, None, "boom")):
        result = hotels_finder(city="Nowhere", checkin_date="2026-09-01", checkout_date="2026-09-08")
    assert result == {"error": "boom"}


def test_hotels_finder_network_error():
    with patch("agents.tools.hotel_finder._resolve_destination", return_value=("123", "city", None)):
        with patch("agents.tools.hotel_finder.requests.get", side_effect=requests.exceptions.ConnectionError("dropped")):
            result = hotels_finder(city="Paris", checkin_date="2026-09-01", checkout_date="2026-09-08")
    assert "error" in result and "Network error" in result["error"]