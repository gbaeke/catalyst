from .base_extractor import BaseExtractor
import ollama
import logging
from typing import Dict, Any
import json
from config import settings

class OllamaExtractor(BaseExtractor):
    def extract(self, template_content: Dict[str, str], input_string: str, template_name: str = None) -> Dict[str, Any]:
        if template_content is None:
            raise ValueError("template_content must not be None")


        json_template = {key: f"a {value} value" for key, value in template_content.items()}
        json_template_str = json.dumps(json_template)

        try:
            completion = ollama.chat(
                model=settings.ollama_model,
                format="json",
                messages=[
                    {"role": "system", "content": f"Extract document details in the following JSON format: {json_template_str}"},
                    {"role": "user", "content": input_string},
                ]
            )
            message = completion['message']['content']

            try:
                parsed_message = json.loads(message)
                return parsed_message
            except json.JSONDecodeError:
                logging.error("Failed to parse the message as JSON.")
                raise ValueError("No invoice details extracted from the document.")
        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")
            return None