import os
import logging
from pusher import Pusher
from .base_handler import BaseOutputHandler
from typing import Dict, Any, Union
from pydantic import BaseModel

class PusherOutputHandler(BaseOutputHandler):
    def __init__(self):
        self.app_id = os.getenv('PUSHER_APP_ID')
        self.key = os.getenv('PUSHER_KEY')
        self.secret = os.getenv('PUSHER_SECRET')
        self.cluster = os.getenv('PUSHER_CLUSTER')
        self.channel = os.getenv('PUSHER_CHANNEL', 'invoice-channel')
        
        if not all([self.app_id, self.key, self.secret, self.cluster]):
            raise ValueError("PUSHER_APP_ID, PUSHER_KEY, PUSHER_SECRET, and PUSHER_CLUSTER must be set")
        
        self.pusher = Pusher(
            app_id=self.app_id,
            key=self.key,
            secret=self.secret,
            cluster=self.cluster,
            ssl=True
        )

    def handle_output(self, blob_name: str, invoice_details: Union[Dict[str, Any], BaseModel]):
        try:
            # Convert Pydantic model to dict if necessary
            if isinstance(invoice_details, BaseModel):
                invoice_details = invoice_details.model_dump()

            # Create a dictionary with blob_name and invoice_details
            output_data = {
                "blob_name": blob_name,
                "invoice_details": invoice_details
            }

            # Push the data to the Pusher channel
            self.pusher.trigger(self.channel, 'invoice-processed', output_data)

            logging.info(f"Invoice details pushed to Pusher channel: {self.channel}")
        except Exception as e:
            logging.error(f"An error occurred while pushing to Pusher: {str(e)}")