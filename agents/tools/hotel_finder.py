import os
import requests
from dotenv import load_dotenv

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
HOST = "booking-com15.p.rapidapi.com"
BASE_URL = f"https://{HOST}/api/v1/hotels"

HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": HOST,
}


def _resolve_destination(query: str):
    """
    Step 1: turn a place name into the dest_id + search_type that
    the real hotel search endpoint requires. Returns (dest_id, search_type, error).
    """
    response = requests.get(f"{BASE_URL}/searchDestination", headers=HEADERS, params={"query": query})
    if response.status_code != 200:
        return None, None, f"Failed to resolve destination: {response.status_code} - {response.text}"

    matches = response.json().get("data", [])
    if not matches:
        return None, None, f"No destination found for '{query}'"

    top_match = matches[0]
    return top_match["dest_id"], top_match["search_type"], None


def hotels_finder(city: str, checkin_date: str, checkout_date: str, adults: int = 1,
                   room_qty: int = 1, currency_code: str = "USD", units: str = "metric",
                   languagecode: str = "en-us"):
    """
    Search hotels via Booking.com (RapidAPI). Two-step: resolve the city name
    to a dest_id/search_type, then search using those.
    """
    dest_id, search_type, error = _resolve_destination(city)
    if error:
        return {"error": error}

    params = {
        "dest_id": dest_id,
        "search_type": search_type,
        "arrival_date": checkin_date,
        "departure_date": checkout_date,
        "adults": adults,
        "room_qty": room_qty,
        "currency_code": currency_code,
        "units": units,
        "languagecode": languagecode,
    }

    response = requests.get(f"{BASE_URL}/searchHotels", headers=HEADERS, params=params)
    if response.status_code != 200:
        return {"error": f"Failed to fetch hotels: {response.status_code} - {response.text}"}

    return response.json()


if __name__ == "__main__":
    result = hotels_finder(city="Paris", checkin_date="2026-09-01", checkout_date="2026-09-08")
    print(result)