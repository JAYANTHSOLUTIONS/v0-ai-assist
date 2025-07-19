import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv(".env.local")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_BASE = "https://api.tripxplo.com/v1/api"
EMAIL = os.getenv("TRIPXPLO_EMAIL")
PASSWORD = os.getenv("TRIPXPLO_PASSWORD")

_token_cache = None

def get_token():
    global _token_cache
    if _token_cache:
        logger.info("Using cached token")
        return _token_cache

    logger.info("Fetching new token from TripXplo API")
    try:
        response = requests.put(
            f"{API_BASE}/admin/auth/login",
            json={"email": EMAIL, "password": PASSWORD},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        # The actual token key in your log was "accessToken" or maybe "jwt"?
        token = data.get("accessToken") or data.get("jwt")
        if not token:
            raise ValueError("No accessToken or jwt found in login response")

        _token_cache = token
        logger.info(f"✅ Logged in successfully. JWT Token:\n{_token_cache}\n")
        return _token_cache
    except Exception as e:
        logger.error(f"Token fetch error: {e}")
        _token_cache = None
        raise

def get_packages(search: str = "", limit: int = 100, offset: int = 0):
    token = get_token()
    params = {"limit": limit, "offset": offset}
    if search:
        params["search"] = search

    try:
        response = requests.get(
            f"{API_BASE}/admin/package",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=10
        )
        response.raise_for_status()
        packages = response.json().get("result", {}).get("docs", [])
        logger.info(f"Fetched {len(packages)} packages with search='{search}'")
        return packages
    except Exception as e:
        logger.error(f"Error fetching packages: {e}")
        return []

def get_package_details(package_id: str):
    token = get_token()
    try:
        response = requests.get(
            f"{API_BASE}/admin/package/{package_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        response.raise_for_status()
        details = response.json().get("result", {})
        logger.info(f"Fetched details for package {package_id}")
        return details
    except Exception as e:
        logger.error(f"Error fetching package details: {e}")
        return {}

def get_package_pricing(package_id: str, params: dict):
    token = get_token()
    try:
        response = requests.post(
            f"{API_BASE}/admin/package/{package_id}/pricing",
            json=params,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        response.raise_for_status()
        pricing = response.json().get("result", {})
        logger.info(f"Fetched pricing for package {package_id} with params {params}")
        return pricing
    except Exception as e:
        logger.error(f"Error fetching package pricing: {e}")
        return {}

def get_available_hotels(package_id: str):
    try:
        package_data = get_package_details(package_id)
        hotels = package_data.get("hotel", [])
        logger.info(f"Fetched {len(hotels)} hotels for package {package_id}")
        return hotels
    except Exception as e:
        logger.error(f"Error fetching hotels: {e}")
        return []

def get_available_vehicles(package_id: str):
    try:
        package_data = get_package_details(package_id)
        vehicles = package_data.get("availableVehicle", [])
        logger.info(f"Fetched {len(vehicles)} vehicles for package {package_id}")
        return vehicles
    except Exception as e:
        logger.error(f"Error fetching vehicles: {e}")
        return []

def get_available_activities(package_id: str):
    try:
        package_data = get_package_details(package_id)
        activities = package_data.get("activity", [])
        logger.info(f"Fetched {len(activities)} activities for package {package_id}")
        return activities
    except Exception as e:
        logger.error(f"Error fetching activities: {e}")
        return []

def get_interests():
    token = get_token()
    try:
        response = requests.get(
            f"{API_BASE}/admin/package/interest/get",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        response.raise_for_status()
        interests = response.json().get("result", [])
        logger.info(f"Fetched {len(interests)} interests")
        return interests
    except Exception as e:
        logger.error(f"Error fetching interests: {e}")
        return []

def search_destinations(search: str = ""):
    token = get_token()
    params = {}
    if search:
        params["search"] = search
    try:
        response = requests.get(
            f"{API_BASE}/admin/package/destination/search",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=10
        )
        response.raise_for_status()
        destinations = response.json().get("result", [])
        logger.info(f"Fetched {len(destinations)} destinations with search='{search}'")
        return destinations
    except Exception as e:
        logger.error(f"Error searching destinations: {e}")
        return []
