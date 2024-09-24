from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, template_content: Dict[str, str], input_string: str, template_name: str = None) -> Dict[str, Any]:
        pass