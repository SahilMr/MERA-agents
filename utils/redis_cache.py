import json
import logging
import redis
from constants.app_constants import RedisConfig

logger = logging.getLogger(__name__)

class ConversationCache:
    def __init__(self):
        try:
            self.client = redis.Redis.from_url(RedisConfig.REDIS_URL, decode_responses=True)
            # Test connection
            self.client.ping()
            logger.info("Connected to Redis cache successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.client = None

    def get_conversation_history(self, user_id: str) -> list:
        """Fetch the last 10 conversational turns for the user."""
        if not self.client:
            return []
            
        key = f"conversation:{user_id}"
        try:
            # Get all elements from the list
            items = self.client.lrange(key, 0, -1)
            # Parse JSON strings back to dicts
            return [json.loads(item) for item in items]
        except Exception as e:
            logger.error(f"Error fetching cache for user {user_id}: {e}")
            return []

    def add_conversation_turn(self, user_id: str, question: str, answer: str):
        """Append a new Q&A pair and maintain max size of 10."""
        if not self.client:
            return
            
        key = f"conversation:{user_id}"
        turn = json.dumps({"question": question, "answer": answer})
        
        try:
            # Right push the new turn
            self.client.rpush(key, turn)
            # Trim the list to keep only the last 10 elements
            # ltrim keeps elements from start_index to end_index.
            # To keep the last 10, we keep from -10 to -1.
            self.client.ltrim(key, -10, -1)
        except Exception as e:
            logger.error(f"Error updating cache for user {user_id}: {e}")
