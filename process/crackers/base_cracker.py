from abc import ABC, abstractmethod
from typing import Any

class BaseCracker(ABC):
    @abstractmethod
    def crack(self, file_content: bytes) -> str:
        pass