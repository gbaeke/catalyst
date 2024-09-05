import os
import logging
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from dapr.clients import DaprClient
import grpc
from pydantic import BaseModel
from azure.storage.blob import BlobServiceClient
import uuid
import json
from typing import Dict, Any, Tuple, Optional

# Set up required inputs for http client to perform service invocation
pubsub_name = os.getenv('PUBSUB_NAME', 'pubsub')
topic_name = os.getenv('TOPIC_NAME', 'invoices')
storage_account_name = os.getenv('STORAGE_ACCOUNT_NAME', 'diagrid')
storage_account_key = os.getenv('STORAGE_ACCOUNT_KEY', '')
container_name = os.getenv('CONTAINER_NAME', 'files')
kvstore_name = os.getenv('KVSTORE_NAME', 'kvstore')

# model for pubsub message about an invoice
#  path: the path to the file in the blob storage
#  template_name: the name of the template to use for processing the invoice (should exist in the kvstore)
class Invoice(BaseModel):
    path: str
    template_name: str  # Added template_name field

app = FastAPI()

logging.basicConfig(level=logging.INFO)

async def upload_to_azure(storage_account_name: str, container_name: str, storage_account_key: str, file: UploadFile):
    """
    Uploads a file to Azure Blob Storage.

    Args:
        storage_account_name (str): The name of the Azure Storage account.
        container_name (str): The name of the container in the Azure Storage account.
        storage_account_key (str): The access key for the Azure Storage account.
        file (UploadFile): The file to be uploaded.

    Returns:
        str: The unique blob name of the uploaded file if successful, None otherwise.

    Raises:
        Exception: If an error occurs during the upload process.
    """
    try:
        # Create the BlobServiceClient object
        blob_service_client = BlobServiceClient(
            f"https://{storage_account_name}.blob.core.windows.net",
            credential=storage_account_key
        )

        # Create a blob client using the local file name as the name for the blob
        file_extension = os.path.splitext(file.filename)[1]
        unique_blob_name = f"{uuid.uuid4()}{file_extension}"
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=unique_blob_name)

        # Upload the file to Azure Blob Storage
        content = await file.read()
        blob_client.upload_blob(content, overwrite=True)

        logging.info(f"File {file.filename} uploaded to Azure Blob Storage successfully.")
        return unique_blob_name
    except Exception as e:
        logging.error(f"An error occurred while uploading to Azure Blob Storage: {str(e)}")
        return None


# Function to publish an invoice via Dapr pub/sub
def publish_invoice(invoice: Invoice):
    """
    Publishes an invoice using Dapr pub/sub.

    Args:
        invoice (Invoice): The invoice object to be published.

    Returns:
        bool: True if the publish was successful, False otherwise.

    This function uses the Dapr Client to publish an event to the 'invoices' topic
    in the specified pub/sub component. The invoice data is serialized to JSON
    before publishing.

    If successful, it logs an info message. If an RPC error occurs, it returns False.
    """
    with DaprClient() as d:
        try:
            result = d.publish_event(
                pubsub_name=pubsub_name,
                topic_name=topic_name,
                data=invoice.model_dump_json(),
                data_content_type='application/json',
            )
            logging.info('Publish Successful. Invoice published: %s' %
                            invoice.path)
            return True
        except grpc.RpcError as err:
            logging.error(f"Failed to publish invoice: {err}")
            return False

@app.get("/")
async def root_status():
    return JSONResponse(content={"status": "ok"}, status_code=200)


@app.post("/template/")
async def submit_template(invoice_input: Dict[str, Any]):
    """
    Endpoint to submit a template for invoice processing.

    This function receives invoice input data, extracts the template name,
    and saves the remaining data to a key/value store using Dapr.

    Args:
        invoice_input (Dict[str, Any]): A dictionary containing the invoice template data.
                                        Must include a 'template_name' key.

    Returns:
        JSONResponse: A JSON response indicating success or failure.

    Raises:
        ValueError: If 'template_name' is missing from the input.
        HTTPException: If there's an error saving to the key/value store.
    """
    try:
        logging.info(f"Invoice input: {invoice_input}")
        
        # extract template name from input
        template_name = invoice_input.get('template_name')

        # a temolate name is required
        if template_name is None:
            logging.error("template_name is missing from invoice_input")
            raise ValueError("template_name is required in the input")

        # Extract other fields in new dict
        invoice_data = invoice_input.copy()
        invoice_data.pop('template_name')

        # Save to Dapr key/value store
        with DaprClient() as d:
            try:
                d.save_state(store_name=kvstore_name,
                                key=template_name, value=str(invoice_data))
            except grpc.RpcError as err:
                logging.error(f"Dapr state store error: {err.details()}")
                raise HTTPException(status_code=500, detail="Failed to save template")

        return JSONResponse(content={"message": "Invoice template saved successfully"}, status_code=200)
    except ValueError as ve:
        logging.error(f"Validation error: {str(ve)}")
        return JSONResponse(content={"message": str(ve)}, status_code=400)
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return JSONResponse(content={"message": "An unexpected error occurred"}, status_code=500)

@app.get("/template/{template_name}")
async def get_template(template_name: str):
    """
    Endpoint to check if a template exists and retrieve its data.
    Also called from process app to retrieve template data
    """
    template_data, error = check_template_exists(template_name)
    if error:
        if error == "Template not found":
            return JSONResponse(content={"message": error}, status_code=404)
        else:
            raise HTTPException(status_code=500, detail=error)
    return JSONResponse(content=template_data, status_code=200)

# can be used from this app to check if a template exists
# used by get_template endpoint
def check_template_exists(template_name: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Check if a template exists and retrieve its data.

    Args:
        template_name (str): The name of the template to retrieve.

    Returns:
        Tuple[Optional[Dict[str, Any]], Optional[str]]: A tuple containing the template data (if found) and an error message (if any).
    """
    try:
        with DaprClient() as d:
            response = d.get_state(store_name=kvstore_name, key=template_name)
            if response.data:
                logging.info(f"Template data: {response.data}")
                template_data = json.loads(response.data.decode("utf-8").replace("'", '"'))
                logging.info(f"Extracted template data: {template_data}")
                return template_data, None
            else:
                return None, "Template not found"
    except grpc.RpcError as err:
        error_message = f"An error occurred while retrieving template: {str(err.details())}"
        logging.error(error_message)
        return None, error_message

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...), template_name: str = Form(...)):
    try:
        # Check if the template exists
        template_data, error = check_template_exists(template_name)
        if error:
            return JSONResponse(content={"message": f"Template error: {error}"}, status_code=400)

        # upload to azure
        blob_name = await upload_to_azure(storage_account_name, container_name, storage_account_key, file)
        if not blob_name:
            raise ValueError("File received but not saved to blob storage nor queued")

        # construct invoice object
        invoice = Invoice(path=blob_name, template_name=template_name)

        # publish invoice
        if not publish_invoice(invoice):
            raise ValueError("File uploaded but failed to publish to queue")
        else:
            return JSONResponse(content={"message": "File uploaded and queued successfully"}, status_code=200)
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return JSONResponse(content={
            "message": f"An error occurred: {str(e)}"
        }, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
