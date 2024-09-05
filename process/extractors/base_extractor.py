from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseInvoiceExtractor(ABC):
    @abstractmethod
    def extract(self, template_content: Dict[str, str], input_string: str) -> Dict[str, Any]:
        pass