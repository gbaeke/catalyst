import os
import logging
from azure.eventgrid import EventGridPublisherClient
from azure.core.messaging import CloudEvent
from azure.core.credentials import AzureKeyCredential
from .base_handler import BaseOutputHandler
from typing import Dict, Any, Union
from pydantic import BaseModel

class EventGridOutputHandler(BaseOutputHandler):
    def __init__(self):
        self.topic_endpoint = os.getenv('EVENT_GRID_TOPIC_ENDPOINT')
        self.topic_key = os.getenv('EVENT_GRID_TOPIC_KEY')
        self.topic_name = os.getenv('EVENT_GRID_TOPIC_NAME')    
        if not self.topic_endpoint or not self.topic_key or not self.topic_name:
            raise ValueError("EVENT_GRID_TOPIC_ENDPOINT, EVENT_GRID_TOPIC_KEY and EVENT_GRID_TOPIC_NAME must be set")
        
        self.client = EventGridPublisherClient(endpoint=self.topic_endpoint, credential=AzureKeyCredential(self.topic_key), 
                                               namespace_topic=self.topic_name)

    def handle_output(self, blob_name: str, invoice_details: Union[Dict[str, Any], BaseModel]):
        try:
            # Convert Pydantic model to dict if necessary
            if isinstance(invoice_details, BaseModel):
                invoice_details = invoice_details.model_dump()

            # Send the event to Event Grid
            self.send_event(
                event_type="Invoice.Processed",
                subject=f"Invoice/{blob_name}",
                data_version="1.0",
                data=invoice_details
            )
            logging.info(f"Invoice details sent to Event Grid for blob: {blob_name}")
        except Exception as e:
            logging.error(f"An error occurred while sending to Event Grid: {str(e)}")

    def send_event(self, event_type: str, subject: str, data_version: str, data: dict = None):
        """
        Sends an event using the EventGridClient.

        Args:
            event_type (str): The type of the event.
            subject (str): The subject of the event.
            data_version (str): The version of the data being sent.
            data (dict, optional): The data to be sent with the event.

        Returns:
            None
        """
        event = CloudEvent(
            type=event_type,
            subject=subject,
            source="process",  # source is required
            data=data
        )
        
        self.client.send(event)