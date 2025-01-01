from .base_extractor import BaseExtractor
import ollama
import logging
from typing import Dict, Any
import json
from config import settings
from pydantic import create_model
from .models.static_invoice import Model

class OllamaExtractor(BaseExtractor):

     # Define MODEL_REGISTRY within the class
    MODEL_REGISTRY = {
        'static_invoice': Model,
        # Add other models here as needed
    }

    def extract(self, template_content: Dict[str, str], input_string: str, template_name: str = None) -> Dict[str, Any]:
        if template_name and template_name in self.MODEL_REGISTRY:
            DynamicModel = self.MODEL_REGISTRY[template_name]
        else:
            type_mapping = {
                'str': str,
                'float': float,
                'bool': bool
            }

            fields = {
                key: (type_mapping[value], ...) for key, value in template_content.items()
            }

            DynamicModel = create_model('DynamicModel', **fields)

        try:
            completion = ollama.chat(
                model=settings.ollama_model,
                format=DynamicModel.model_json_schema(),
                messages=[
                    {"role": "system", "content": f"Extract document details"},
                    {"role": "user", "content": input_string},
                ],
                options={
                    "temperature": 0,
                    "num_predict": 2000  # there is no max_tokens in ollama
                }
            )
            

            try:
                document = DynamicModel.model_validate_json(completion.message.content)
                return document.model_dump()
            except Exception as e:
                logging.error("Failed to parse the message as JSON.")
                raise ValueError("No details extracted from the document.")
        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")
            return None