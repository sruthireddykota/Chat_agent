from urllib.parse import quote

import requests

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def get_chat_history(
    session_id: str,
    limit: int = 9,
    authorization: str | None = None,
):
    """Retrieve conversation history through the FastAPI conversation API"""
    if not session_id:
        logger.warning("Cannot retrieve chat history without a session_id")
        return []

    base_url = settings.API_BASE_URL.rstrip("/")
    encoded_session_id = quote(session_id, safe="")
    url = f"{base_url}/api/v1/sessions/{encoded_session_id}/conversation-messages"

    try:
        headers = {"Authorization": authorization} if authorization else {}
        response = requests.get(
            url,
            params={"limit": max(1, int(limit))},
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        messages = payload.get("messages", [])

        if not isinstance(messages, list):
            logger.error(
                "Conversation API returned an invalid messages payload for %s: %s",
                session_id,
                type(messages).__name__,
            )
            return []

        logger.info(
            "Conversation API returned %d messages for session %s",
            len(messages),
            session_id,
        )
        return messages
    except requests.RequestException as exc:
        body = getattr(exc.response, "text", "")[:300] if exc.response is not None else ""
        logger.error(
            "Conversation API request failed for session %s (url=%s): %s%s",
            session_id,
            url,
            exc,
            f" response={body}" if body else "",
        )
    except (TypeError, ValueError) as exc:
        logger.error("Invalid conversation API response for session %s: %s", session_id, exc)
    except Exception as exc:
        logger.error("Error retrieving chat history for session %s: %s", session_id, exc, exc_info=True)

    return []
