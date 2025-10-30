import logging
import threading

logger = logging.getLogger(__name__)


class ApiKeyManager:
    def __init__(self, keys: list[str]):
        self.keys = list(filter(None, keys))
        self.available_keys = list(set(self.keys))
        self.lock = threading.Condition()

        self._validate()

    def get(self):
        with self.lock:
            logger.debug(f'get from: {len(self.available_keys)}')
            while not self.available_keys:
                self.lock.wait()

            return self.available_keys.pop(0)

    def release(self, key: str):
        if key not in self.keys:
            return

        with self.lock:
            logger.debug(f'release to: {len(self.available_keys)}')
            if key not in self.available_keys:
                self.available_keys.append(key)
                self.lock.notify()

    def _validate(self):
        if not self.keys:
            raise ValueError(f'No API keys found for environment variable: {self.env_key}')
