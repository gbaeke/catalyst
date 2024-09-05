import os
import csv
import logging
from .base_handler import BaseOutputHandler
from typing import Dict, Any, Union
from pydantic import BaseModel

class CSVOutputHandler(BaseOutputHandler):
    def __init__(self, filename='invoice_details.csv'):
        self.filename = filename

    def handle_output(self, blob_name: str, invoice_details: Union[Dict[str, Any], BaseModel]):
        try:
            # Convert Pydantic model to dict if necessary
            if isinstance(invoice_details, BaseModel):
                invoice_details = invoice_details.dict()

            # Format invoice details as a single string
            details_str = ' '.join([f"{k}={v!r}" for k, v in invoice_details.items()])

            file_exists = os.path.isfile(self.filename)
            with open(self.filename, 'a', newline='') as f:
                writer = csv.writer(f, quoting=csv.QUOTE_ALL)
                if not file_exists:
                    writer.writerow(['Blob Name', 'Invoice Details'])
                
                writer.writerow([blob_name, details_str])
            logging.info(f"Invoice details written to CSV: {self.filename}")
        except Exception as e:
            logging.error(f"An error occurred while writing to CSV: {str(e)}")