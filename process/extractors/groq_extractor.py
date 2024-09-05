from .base_extractor import BaseInvoiceExtractor
from typing import Dict, Any
import logging
from groq import Groq
import os
import json

class GroqInvoiceExtractor(BaseInvoiceExtractor):
    def __init__(self):
        self.client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        pass

    def extract(self, template_content: Dict[str, str], input_string: str) -> Dict[str, Any]:
        
        # generate the prompt that includes the fields to extract
        prompt = "Extract the following fields from a given invoice. Return the fields in JSON format:\n"
        for field, field_type in template_content.items():
            prompt += f"- {field} ({field_type})\n"
        prompt = prompt.strip()

        try:
            completion = self.client.chat.completions.create(
                model="llama3-8b-8192",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": input_string},
                ],
                max_tokens=2000,
                temperature=0,
            )
            message = completion.choices[0].message.content
       
            
            try:
                extracted_data = json.loads(message)
                return extracted_data
            except json.JSONDecodeError:
                raise Exception("Failed to parse GROQ response as JSON")
        except Exception as e:
            logging.error(f"An error occurred during GROQ extraction: {str(e)}")
            return None