import os
import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, create_model
from typing import Any, Dict, Type
from azure.storage.blob import BlobServiceClient
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult, AnalyzeDocumentRequest
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
import requests
from extractors.extractor_factory import InvoiceExtractorFactory
from output_handlers.handler_factory import OutputHandlerFactory
from output_handlers.json_handler import JSONOutputHandler
from extractors.groq_extractor import GroqInvoiceExtractor

# Set up required inputs for http client to perform service invocation
base_url = os.getenv('DAPR_HTTP_ENDPOINT', 'http://localhost')
dapr_api_token = os.getenv('DAPR_API_TOKEN', '')
pubsub_name = os.getenv('PUBSUB_NAME', 'pubsub')
storage_account_name = os.getenv('STORAGE_ACCOUNT_NAME', '')
storage_account_key = os.getenv('STORAGE_ACCOUNT_KEY', '')
container_name = os.getenv('CONTAINER_NAME', '')
docint_key = os.getenv('DOCINT_KEY', '')
docint_url = os.getenv('DOCINT_URL', '')
openai_key = os.getenv('OPENAI_KEY', '')
kvstore_name = os.getenv('KVSTORE_NAME', 'kvstore')
invoke_target_appid = os.getenv('INVOKE_APPID', 'upload')
base_url = os.getenv('DAPR_HTTP_ENDPOINT', 'http://localhost')
azure_openai_key = os.getenv('AZURE_OPENAI_KEY', '')
azure_openai_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT', '')
azure_openai_model = os.getenv('AZURE_OPENAI_MODEL', '')
azure_openai_api_version = os.getenv('AZURE_OPENAI_API_VERSION', '')

# Add this new environment variable
extractor_type = os.getenv('INVOICE_EXTRACTOR_TYPE', 'groq')
output_handler_type = os.getenv('INVOICE_OUTPUT_HANDLER', 'csv')

app = FastAPI()

logging.basicConfig(level=logging.INFO)

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

def extract_invoice_details(template_content: Dict[str, str], input_string: str):
    extractor = InvoiceExtractorFactory.get_extractor(extractor_type)
    return extractor.extract(template_content, input_string)

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

    # use dapr invoke but use generic http client with required dapr headers
    headers = {'dapr-app-id': invoke_target_appid, 'dapr-api-token': dapr_api_token,
               'content-type': 'application/json'}

    
    try:
        result = requests.get(
            url='%s/template/%s' % (base_url, template_name),
            headers=headers
        )

        if result.ok:
            logging.info('Invocation successful with status code: %s' %
                         result.status_code)
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
    file_content = retrieve_file_from_azure(storage_account_name, container_name, storage_account_key, blob_name)
    
    if file_content is None:
        logging.error(f"Failed to retrieve file from Azure Blob Storage: {blob_name}")
        raise FileNotFoundError(f"Failed to retrieve file from Azure Blob Storage: {blob_name}")
    
    try:
        # use Azure Document Intelligence to extract the text from the file
        document_intelligence_client = DocumentIntelligenceClient(
            endpoint=docint_url, credential=AzureKeyCredential(docint_key)
        )

        doc_request = AnalyzeDocumentRequest(bytes_source=file_content)

        poller = document_intelligence_client.begin_analyze_document(
            "prebuilt-layout", doc_request
        )

        result: AnalyzeResult = poller.result(timeout=30)

        # extract all lines and add them to one string
        lines = [line.content for page in result.pages for line in page.lines]
        lines_str = "\n".join(lines)

        # retrieve the template from the kvstore
        template_content = retrieve_template_from_kvstore(template_name)

        if template_content is None:
            raise IOError(f"Failed to retrieve template from Dapr KV store: {template_name}")

        # extract invoice details using OpenAI and new gpt-4o model with structured response
        invoice_details = extract_invoice_details(template_content, lines_str)

        if not invoice_details:
            raise ValueError("No invoice details extracted from the document.")
        else:
            logging.info(f"Extracted invoice details: {invoice_details}")

            # Use the JSON output handler
            output_handler = OutputHandlerFactory.get_handler(output_handler_type)
            output_handler.handle_output(blob_name, invoice_details)

    except Exception as e:
        logging.error(f"An error occurred during document processing: {str(e)}")
        raise

    # return 200 ok to indicate successful processing of message
    return {'success': True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)