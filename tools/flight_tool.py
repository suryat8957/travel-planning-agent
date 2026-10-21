
import os
import json
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

AVIATIONSTACK_API_KEY = os.getenv("AVIATIONSTACK_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not AVIATIONSTACK_API_KEY:
    raise ValueError("Missing AVIATIONSTACK_API_KEY in your .env file")

if not GOOGLE_API_KEY:
    raise ValueError("Missing GOOGLE_API_KEY in your .env file")

llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    temperature=0,
)


def extract_route(query: str) -> dict:
    """Extract origin and destination airport codes from a travel request."""

    prompt = f"""
Extract the flight route from this user request:
{query!r}

Return ONLY valid JSON with these keys:
{{
  "origin_city": "city name",
  "origin_country": "country name",
  "origin_iata": "three-letter airport code",
  "destination_city": "city name",
  "destination_country": "country name",
  "destination_iata": "three-letter airport code"
}}

Use the most likely major commercial airport for each city.
Use real IATA airport codes. Do not invent codes.
If the route is unclear, return {{}}.
"""

    response = llm.invoke(prompt)
    content = response.content

    if isinstance(content, list):
        content = "\n".join(
            item.get("text", "")
            for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        )

    content = str(content).strip()
    content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content)

    try:
        route = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Could not extract the flight route. Please specify the "
            "origin and destination cities."
        ) from exc

    required = [
        "origin_city",
        "origin_iata",
        "destination_city",
        "destination_iata",
    ]

    if not isinstance(route, dict) or any(
        not route.get(key) for key in required
    ):
        raise ValueError(
            "Route is unclear. Please provide both departure and "
            "destination cities."
        )

    for key in ("origin_iata", "destination_iata"):
        route[key] = str(route[key]).strip().upper()
        if not re.fullmatch(r"[A-Z]{3}", route[key]):
            raise ValueError(f"Invalid airport code returned for {key}.")

    if route["origin_iata"] == route["destination_iata"]:
        raise ValueError("Origin and destination airports are the same.")

    return route


def format_local_time(value: str, timezone_name: str) -> str:
    """Format an API timestamp in the airport's local time zone."""

    if not value:
        return "Unknown"

    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        try:
            dt = dt.astimezone(ZoneInfo(timezone_name))
        except (KeyError, ValueError):
            dt = dt.astimezone(timezone.utc)

        return dt.strftime("%d %b %Y, %I:%M %p %Z")

    except (ValueError, TypeError, OverflowError):
        return value


def search_flight(query: str) -> str:
    """Search Aviationstack flight records for the requested route."""

    try:
        route = extract_route(query)
    except (ValueError, requests.RequestException) as exc:
        return f"Unable to identify the flight route: {exc}"

    origin = route["origin_city"]
    destination = route["destination_city"]

    url = "https://api.aviationstack.com/v1/flights"

    params = {
        "access_key": AVIATIONSTACK_API_KEY,
        "dep_iata": route["origin_iata"],
        "arr_iata": route["destination_iata"],
        "limit": 100,
    }

    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        return f"Flight API request failed: {exc}"
    except ValueError:
        return "Flight API returned invalid JSON."

    if payload.get("error"):
        return f"Flight API error: {payload['error']}"

    records = payload.get("data", [])

    if not records:
        return (
            f"No flight records found for {origin} to {destination}. "
            "This does not necessarily mean no bookable flights exist."
        )

    now = datetime.now(timezone.utc)
    flights = []
    seen = set()

    for flight in records:
        airline_data = flight.get("airline") or {}
        flight_info = flight.get("flight") or {}
        departure = flight.get("departure") or {}
        arrival = flight.get("arrival") or {}

        airline = airline_data.get("name")
        flight_number = flight_info.get("iata")
        departure_time = departure.get("scheduled")
        arrival_time = arrival.get("scheduled")
        status = (flight.get("flight_status") or "unknown").lower()

        if not airline or not flight_number or not departure_time:
            continue

        if status in {"cancelled", "landed"}:
            continue

        try:
            departure_dt = datetime.fromisoformat(
                departure_time.replace("Z", "+00:00")
            )

            if departure_dt.tzinfo is None:
                departure_dt = departure_dt.replace(tzinfo=timezone.utc)

            if departure_dt.astimezone(timezone.utc) < now:
                continue

        except (ValueError, TypeError, AttributeError):
            continue

        unique_key = (flight_number, departure_time)

        if unique_key in seen:
            continue

        seen.add(unique_key)

        flights.append(
            "\n".join([
                f"Airline: {airline}",
                f"Flight number: {flight_number}",
                f"Departure airport: "
                f"{departure.get('airport') or 'Unknown'}",
                f"Departure time: {format_local_time(departure_time, departure.get('timezone') or 'UTC')}",
                f"Arrival airport: "
                f"{arrival.get('airport') or 'Unknown'}",
                f"Arrival time: {format_local_time(arrival_time, arrival.get('timezone') or 'UTC')}",
                f"Status: {status}",
            ])
        )

        if len(flights) >= 5:
            break

    if not flights:
        return (
            f"No matching future flight records were found for "
            f"{origin} to {destination}. Check an airline or booking "
            "provider for bookable flights and current fares."
        )

    return (
        f"Route: {origin}, {route.get('origin_country', '')} "
        f"({route['origin_iata']}) to {destination}, "
        f"{route.get('destination_country', '')} "
        f"({route['destination_iata']})\n\n"
        + "\n\n".join(flights)
        + "\n\nImportant: These are API flight records, not confirmed "
        "booking availability or ticket prices. Verify dates, schedules, "
        "availability, and fares with an airline or booking provider."
    )
