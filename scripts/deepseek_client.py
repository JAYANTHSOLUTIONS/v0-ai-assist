"""DeepSeek LLM client for natural language understanding and generation."""
import json
import httpx
from typing import Dict, Any, List, Optional
from loguru import logger
import re  # Import regex module

from config import settings
from models import ExtractedEntities, IntentType, UIElement


class DeepSeekClient:
    """Client for interacting with DeepSeek LLM API."""

    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.base_url = settings.DEEPSEEK_BASE_URL.rstrip("/")
        self.model = settings.DEEPSEEK_MODEL
        self.client = httpx.AsyncClient(timeout=30.0)

    def _extract_json_from_markdown(self, text: str) -> str:
        match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            logger.debug("Extracted JSON from markdown block successfully.")
            return match.group(1).strip()
        logger.warning(f"No JSON markdown block found. Using raw text:\n{text}")
        return text

    async def _make_request(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 1000
        }

        logger.debug(f"Sending payload to DeepSeek API:\n{json.dumps(payload, indent=2)}")

        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            raw_text = response.text
            logger.debug(f"Raw response body:\n{raw_text}")

            result = json.loads(raw_text)

            choices = result.get("choices")
            if not choices or not isinstance(choices, list):
                raise Exception("Invalid response structure from DeepSeek API: Missing 'choices'")

            message_content = choices[0].get("message", {}).get("content")
            if message_content is None or not message_content.strip():
                raise Exception("Empty or missing message content from DeepSeek API")

            return message_content

        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            logger.error(f"Response content was: {response.text if 'response' in locals() else 'No response'}")
            raise

    async def extract_intent_and_entities(
        self,
        user_input: str,
        conversation_history: Optional[List[str]] = None
    ) -> ExtractedEntities:
        system_prompt = """You are a travel assistant AI that extracts intent and entities from user messages.

Available intents:
- search_flight: User wants to search for flights
- search_hotel: User wants to search for hotels
- book_trip: User wants to book a flight, hotel, or package
- general_inquiry: General travel questions
- greeting: Greetings or casual conversation

Extract the following entities when relevant:
- origin: departure city/airport
- destination: arrival city/airport
- departure_date: departure date
- return_date: return date
- check_in: hotel check-in date
- check_out: hotel check-out date
- passengers: number of passengers
- guests: number of hotel guests
- rooms: number of hotel rooms
- location: hotel location
- class_type: flight class (economy, business, first)
- package: destination/location name for a travel package

Return a JSON object with:
{
    "intent": "intent_name",
    "confidence": 0.0-1.0,
    "entities": {"entity_name": "value", ...}
}
Ensure the JSON is wrapped in a '```json' markdown block.
"""

        messages = [
            {"role": "system", "content": system_prompt}
        ]

        if conversation_history:
            context = "\n".join(conversation_history[-3:])
            messages.append({"role": "user", "content": f"Previous context: {context}"})

        messages.append({"role": "user", "content": f"Extract intent and entities from: '{user_input}'"})

        try:
            response = await self._make_request(messages, temperature=0.3)
            if not response.strip():
                raise Exception("Empty response content from DeepSeek")

            json_string = self._extract_json_from_markdown(response)
            parsed = json.loads(json_string)

            return ExtractedEntities(
                intent=IntentType(parsed["intent"]),
                confidence=parsed.get("confidence", 0.0),
                entities=parsed.get("entities", {})
            )

        except Exception as e:
            logger.error(f"Intent extraction error: {e}")
            return ExtractedEntities(
                intent=IntentType.GENERAL_INQUIRY,
                confidence=0.5,
                entities={}
            )

    async def generate_response(
        self,
        user_input: str,
        intent: IntentType,
        entities: Dict[str, Any],
        api_results: Optional[List[Dict[str, Any]]] = None,
        conversation_history: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        system_prompt = """You are a helpful travel assistant AI. Generate natural, conversational responses.

When providing search results, include relevant UI elements:
- buttons for booking actions
- links for more details
- cards for displaying options

If the user intent involves a travel package (e.g., list or book packages), generate a list of packages with name, price, duration, and destination.

UI element format:
{
    "type": "button|link|card",
    "text": "display text",
    "action": "action_name",
    "data": {"key": "value"}
}

Return JSON with:
{
    "message": "natural language response",
    "ui_elements": [ui_element_objects]
}
Ensure the JSON is wrapped in a '```json' markdown block.
"""

        context_parts = [
            f"User input: {user_input}",
            f"Detected intent: {intent.value}",
            f"Extracted entities: {json.dumps(entities)}"
        ]

        if api_results:
            context_parts.append(f"API results: {json.dumps(api_results)}")

        if conversation_history:
            context_parts.append(f"Recent conversation: {' | '.join(conversation_history[-3:])}")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "\n".join(context_parts)}
        ]

        try:
            response = await self._make_request(messages, temperature=0.8)
            if not response.strip():
                raise Exception("Empty response content from DeepSeek")

            json_string = self._extract_json_from_markdown(response)
            parsed = json.loads(json_string)

            ui_elements = []
            if "ui_elements" in parsed and isinstance(parsed["ui_elements"], list):
                for element in parsed["ui_elements"]:
                    ui_elements.append(UIElement(**element))

            return {
                "message": parsed.get("message", ""),
                "ui_elements": ui_elements
            }

        except Exception as e:
            logger.error(f"Response generation error: {e}")
            return {
                "message": "I apologize, but I'm having trouble processing your request right now. Please try again.",
                "ui_elements": []
            }


# Global DeepSeek client instance
deepseek_client = DeepSeekClient()