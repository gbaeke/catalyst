from abc import ABC, abstractmethod
from typing import Dict, Any, Union
from pydantic import BaseModel

class BaseOutputHandler(ABC):
    @abstractmethod
    def handle_output(self, blob_name: str, invoice_details: Union[Dict[str, Any], BaseModel]):
        pass