import json
import logging
from .base_handler import BaseOutputHandler
from typing import Dict, Any, Union
from pydantic import BaseModel

class JSONOutputHandler(BaseOutputHandler):
    def __init__(self, filename='invoice_details.jsonl'):
        self.filename = filename

    def handle_output(self, blob_name: str, invoice_details: Union[Dict[str, Any], BaseModel]):
        try:
            # Convert Pydantic model to dict if necessary
            if isinstance(invoice_details, BaseModel):
                invoice_details = invoice_details.dict()

            # Create a dictionary with blob_name and invoice_details
            output_data = {
                "blob_name": blob_name,
                "invoice_details": invoice_details
            }

            # Append new data as a single line JSON
            with open(self.filename, 'a') as f:
                f.write(json.dumps(output_data) + '\n')

            logging.info(f"Invoice details appended to JSONL: {self.filename}")
        except Exception as e:
            logging.error(f"An error occurred while writing to JSONL: {str(e)}")