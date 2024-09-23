from .base_extractor import BaseInvoiceExtractor
from typing import Dict, Any, Type
from openai import AzureOpenAI
from pydantic import create_model, BaseModel
import logging
import os
from .models.static_invoice import Model  # Updated import path

class OpenAIInvoiceExtractor(BaseInvoiceExtractor):
    # Define MODEL_REGISTRY within the class
    MODEL_REGISTRY = {
        'static_invoice': Model,
        # Add other models here as needed
    }

    def __init__(self):
        self.client = AzureOpenAI(
            azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT', ''),
            azure_deployment=os.getenv('AZURE_OPENAI_MODEL', ''),
            api_version=os.getenv('AZURE_OPENAI_API_VERSION', ''),
            api_key=os.getenv('AZURE_OPENAI_KEY', '')
        )

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
            completion = self.client.beta.chat.completions.parse(
                model="gpt-4o",
                response_format=DynamicModel,
                messages=[
                    {"role": "system", "content": "Extract invoice details"},
                    {"role": "user", "content": input_string},
                ],
                max_tokens=2000,
                temperature=0,
            )
            message = completion.choices[0].message

            if message.parsed:
                return message.parsed
            else:
                logging.error("No invoice details extracted from the document.")
                return None
        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")
            return None