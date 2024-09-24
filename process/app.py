import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Any, Dict
from azure.storage.blob import BlobServiceClient
import requests
from output_handlers.handler_factory import OutputHandlerFactory
from extractors.extractor_factory import InvoiceExtractorFactory
from extractors.openai_extractor import OpenAIInvoiceExtractor
from config import settings  # gets settings from environment variables
from crackers.cracker_factory import CrackerFactory

app = FastAPI()

logging.basicConfig(level=logging.INFO)

# Mount the static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/ui")
async def read_index():
    return FileResponse("static/index.html")

# model for pub/sub data field
#  path: the path to the file in the blob storage (file will be downloaded from blob storage)
#  template_name: the name of the template to use for processing the invoice (should exist in the kvstore)
class Invoice(BaseModel):
    path: str
    template_name: str

# pub/sub uses CloudEvent; Invoice above is the data
class CloudEvent(BaseModel):
    datacontenttype: str
    source: str
    topic: str
    pubsubname: str
    data: dict
    id: str
    specversion: str
    tracestate: str
    type: str
    traceid: str

def extract_invoice_details(template_content: Dict[str, str], input_string: str, template_name: str):
    extractor = InvoiceExtractorFactory.get_extractor(settings.extractor_type)
    return extractor.extract(template_content, input_string, template_name)

def retrieve_file_from_azure(storage_account_name: str, container_name: str, storage_account_key: str, blob_name: str) -> bytes:
    try:
        blob_service_client = BlobServiceClient(account_url=f"https://{storage_account_name}.blob.core.windows.net", credential=storage_account_key)
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        
        download_stream = blob_client.download_blob()
        file_content = download_stream.readall()
        
        logging.info(f"File {blob_name} retrieved from Azure Blob Storage successfully.")
        return file_content
    except Exception as e:
        logging.error(f"An error occurred while retrieving from Azure Blob Storage: {str(e)}")
        return None
    
def retrieve_template_from_kvstore(template_name: str):
    headers = {'dapr-app-id': settings.invoke_target_appid, 'content-type': 'application/json'}
    if settings.dapr_api_token:
        headers['dapr-api-token'] = settings.dapr_api_token

    try:
        result = requests.get(
            url=f'{settings.dapr_http_endpoint}{":" + settings.dapr_http_port if not settings.dapr_api_token else ""}/template/{template_name}',
            headers=headers,
            timeout=60
        )

        if result.ok:
            logging.info('Invocation successful with status code: %s' % result.status_code)
            logging.info(f"Template retrieved: {result.json()}")
            return result.json()

    except Exception as e:
        logging.error(f"An error occurred while retrieving template from Dapr KV store: {str(e)}")
        return None

@app.get("/")
async def root_status():
    return JSONResponse(content={"status": "ok"}, status_code=200)

@app.post('/process')  # called by pub/sub when a new invoice is uploaded
async def consume_orders(event: CloudEvent):
    blob_name = event.data['path']
    template_name = event.data['template_name']
    logging.info(f'Invoice received: {blob_name}, Template name: {template_name}')

    # retrieve the file from the blob storage
    file_content = retrieve_file_from_azure(settings.storage_account_name, settings.container_name, settings.storage_account_key, blob_name)
    
    if file_content is None:
        logging.error(f"Failed to retrieve file from Azure Blob Storage: {blob_name}")
        raise FileNotFoundError(f"Failed to retrieve file from Azure Blob Storage: {blob_name}")
    
    try:
        # use the appropriate cracker to extract the text from the file
        logging.info(f"Using cracker: {settings.cracker_type}")
        cracker = CrackerFactory.get_cracker(settings.cracker_type)
        lines_str = cracker.crack(file_content)

        logging.info(f"{settings.cracker_type.capitalize()} processing completed successfully.")

        # retrieve the template from the kvstore
        template_content = None
        if template_name not in OpenAIInvoiceExtractor.MODEL_REGISTRY:
            logging.info(f"Using model from KV store: {template_name}")
            template_content = retrieve_template_from_kvstore(template_name)
            logging.info(f"Template retrieved from KV store: {template_content}")
            if template_content is None:
                raise IOError(f"Failed to retrieve template from Dapr KV store: {template_name}")
        else:
            logging.info(f"Using static model: {template_name}")
            
        # extract invoice details with specified extractor
        invoice_details = extract_invoice_details(template_content, lines_str, template_name)

        if not invoice_details:
            raise ValueError("No invoice details extracted from the document.")
        else:
            logging.info(f"Extracted invoice details: {invoice_details}")

            # Use the appropriate output handlers
            output_handlers = OutputHandlerFactory.get_handlers(settings.output_handler_types)
            for handler in output_handlers:
                handler.handle_output(blob_name, invoice_details)
    except Exception as e:
        logging.error(f"An error occurred during document processing: {str(e)}")
        # Return a 500 Internal Server Error response
        return JSONResponse(
            status_code=500,
            content={"error": "An internal server error occurred during document processing."}
        )

    # return 200 ok to indicate successful processing of message
    return {'success': True}

# this is used when you use Dapr directly instead of catalyst
@app.get("/dapr/subscribe")
async def subscribe():
    logging.info(f"Subscribing to topic 'invoices' with pubsub name '{settings.pubsub_name}' and route '/process'")
    subscriptions = [
        {
            'pubsubname': settings.pubsub_name,
            'topic': 'invoices',
            'route': '/process'
        }
    ]
    return JSONResponse(content=subscriptions)

@app.get("/static/index.html")
async def read_index():
    return FileResponse("static/index.html")

@app.post("/extract")
async def extract_invoice(template_content: Dict[str, str], input_string: str, model_name: str = None):
    result = extract_invoice_details(template_content, input_string)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)