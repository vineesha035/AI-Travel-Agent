import os
import requests
from dotenv import load_dotenv

load_dotenv()
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
BASE_URL = "https://skyscanner-flights4.p.rapidapi.com/api/v1"

HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": "skyscanner-flights4.p.rapidapi.com",
}
def flights_finder(origin: str, destination: str, date: str, return_date: str = None,
                    adults: int = 1, cabin: str = "economy", currency: str = "USD",
                    market: str = "US", locale: str = "en-US", limit: int = 20):
    """
    Search flights via the Skyscanner Flights API (RapidAPI).
    Uses the round-trip endpoint if return_date is given, otherwise one-way.
    """
    params = {
        "origin": origin,
        "destination": destination,
        "date": date,
        "adults": adults,
        "cabin": cabin,
        "currency": currency,
        "market": market,
        "locale": locale,
        "limit": limit,
    }

    if return_date:
        endpoint = f"{BASE_URL}/roundtrip"
        params["return_date"] = return_date
    else:
        endpoint = f"{BASE_URL}/search"

    response = requests.get(endpoint, headers=HEADERS, params=params)

    if response.status_code != 200:
        return {"error": f"Failed to fetch flights: {response.status_code} - {response.text}"}

    return response.json()
if __name__ == "__main__":
    result = flights_finder(origin="JFK", destination="LHR", date="2026-09-01", return_date="2026-09-08")
    print(result)