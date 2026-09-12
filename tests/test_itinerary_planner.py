from unittest.mock import patch, MagicMock
from agents.tools.itinerary_planner import itinerary_planner


def test_itinerary_planner_success():
    fake_response = MagicMock(content="A lovely itinerary.")
    with patch("agents.tools.itinerary_planner._call_llm", return_value=fake_response):
        result = itinerary_planner(destination="Paris", dates=["2026-09-01", "2026-09-08"],
                                    interests="museums", flights={}, hotels={})
    assert result == {"itinerary": "A lovely itinerary."}


def test_itinerary_planner_handles_repeated_failure():
    with patch("agents.tools.itinerary_planner._call_llm", side_effect=Exception("model down")):
        result = itinerary_planner(destination="Paris", dates=["2026-09-01", "2026-09-08"],
                                    interests="museums", flights={}, hotels={})
    assert "Could not generate itinerary" in result["itinerary"]
    