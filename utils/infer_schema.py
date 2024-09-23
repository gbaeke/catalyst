import sys
import json
import os
from typing import Dict, Any
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult, AnalyzeDocumentRequest
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
import asyncio

from dotenv import load_dotenv

# you can use datamodel-codegen --input invoice.json --input-file-type jsonschema --output model.py
# the above takes the json schema and creates a Pydantic model in model.py

# Load environment variables from .env file
load_dotenv()

# Get environment variables
docint_key = os.getenv('DOCINT_KEY')
docint_url = os.getenv('DOCINT_URL')
azure_openai_key = os.getenv('AZURE_OPENAI_KEY')
azure_openai_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
azure_openai_model = os.getenv('AZURE_OPENAI_MODEL')
azure_openai_api_version = os.getenv('AZURE_OPENAI_API_VERSION')

# Validate environment variables
if not all([docint_key, docint_url, azure_openai_key, azure_openai_endpoint, azure_openai_model, azure_openai_api_version]):
    raise ValueError("Missing required environment variables. Please check your .env file.")


async def extract_text_from_document(file_path: str) -> str:
    # Initialize the Document Intelligence client
    
    if not docint_key or not docint_url:
        raise ValueError("Document Intelligence credentials are missing. Please check your environment variables.")
    
    try:
        document_intelligence_client = DocumentIntelligenceClient(
            endpoint=docint_url, credential=AzureKeyCredential(docint_key)
        )
    except Exception as e:
        raise ConnectionError(f"Failed to initialize Document Intelligence client: {str(e)}")
    
    try:
        with open(file_path, "rb") as f:
            file_content = f.read()
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {str(e)}")
    
    doc_request = AnalyzeDocumentRequest(bytes_source=file_content)
    
    try:
        poller = document_intelligence_client.begin_analyze_document(
            "prebuilt-layout", doc_request
        )
        
        result: AnalyzeResult = poller.result()
    except Exception as e:
        raise RuntimeError(f"Error analyzing document: {str(e)}")
    
    if not result.pages:
        raise ValueError("No pages found in the document")
    
    lines = [line.content for page in result.pages for line in page.lines]
    if not lines:
        raise ValueError("No text content found in the document")
    
    return "\n".join(lines)

async def generate_json_schema(text: str) -> Dict[str, Any]:
    client = AzureOpenAI(
        azure_endpoint=azure_openai_endpoint,
        api_version=azure_openai_api_version,
        api_key=azure_openai_key
    )
    
    prompt = f"Given the following document text, generate a JSON schema that represents the structure of the document:\n\n{text}\n\nJSON Schema:"
    
    try:
        response = client.chat.completions.create(
            model=azure_openai_model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates JSON schemas based on document text."},
                {"role": "user", "content": prompt}
            ],
            response_format={'type': 'json_object'},
            max_tokens=2000,
            temperature=0
        )
        
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"An error occurred while generating JSON schema: {str(e)}", file=sys.stderr)
        return None

async def main(file_path: str) -> None:
    try:
        text = await extract_text_from_document(file_path)
        schema = await generate_json_schema(text)
        if schema:
            print(json.dumps(schema, indent=2))
        else:
            print("Failed to generate JSON schema.", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python infer_schema.py <input_file_path>", file=sys.stderr)
        sys.exit(1)
    
    asyncio.run(main(sys.argv[1]))
