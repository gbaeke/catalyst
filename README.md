# Catalyst demo: LLM document extraction asynchronous pipeline

This is a demo of a document processing pipeline that uses Dapr to orchestrate an asynchronous pipeline of document processing tasks. Instead of installing Dapr on the local machine or Kubernetes, this demo uses Catalyst. Catalyst is a Dapr-compatible  cloud-based runtime. Here we use it to build and run the app locally but you can also deploy these services to the cloud.

To run the demo, you need to install the diagrid CLI, authenticate and ensure the correct project is selected. Next, run diagrid dev scaffold. That creates a dev-idpdemo.yaml file in the current directory. It looks like this:

```yaml
project: idpdemo
apps:
- appId: process
  disabled: true
  appPort: 8001
  env:
    DAPR_API_TOKEN: [Dapr API token for authentication - should be set by scaffold]
    DAPR_APP_ID: [Identifier for the Dapr application - should be set by scaffold]
    DAPR_CLIENT_TIMEOUT_SECONDS: [Timeout duration for Dapr client in seconds]
    DAPR_GRPC_ENDPOINT: [gRPC endpoint for Dapr communication - should be set by scaffold]
    DAPR_HTTP_ENDPOINT: [HTTP endpoint for Dapr communication - should be set by scaffold]
    STORAGE_ACCOUNT_NAME: [Name of the Azure storage account]
    STORAGE_ACCOUNT_KEY: [Access key for the Azure storage account]
    CONTAINER_NAME: [Name of the container in Azure storage]
    DOCINT_KEY: [API key for document intelligence service]
    DOCINT_URL: [URL for document intelligence service]
    OPENAI_KEY: [API key for OpenAI service]
    AZURE_OPENAI_KEY: [API key for Azure OpenAI service]
    AZURE_OPENAI_ENDPOINT: [Endpoint URL for Azure OpenAI service]
    AZURE_OPENAI_MODEL: [Specific model to use with Azure OpenAI]
    AZURE_OPENAI_API_VERSION: [API version for Azure OpenAI service]
    INVOICE_EXTRACTOR_TYPE: [Type of invoice extractor to use]
    INVOICE_OUTPUT_HANDLER: [Type of output handler for invoice processing]
    GROQ_API_KEY: [API key for Groq service]
  workDir: process
  command: ["python", "app.py"]
- appId: upload
  appPort: 8000
  env:
    DAPR_API_TOKEN: [Dapr API token for authentication - should be set by scaffold]
    DAPR_APP_ID: [Identifier for the Dapr application - should be set by scaffold]
    DAPR_CLIENT_TIMEOUT_SECONDS: [Timeout duration for Dapr client in seconds]
    DAPR_GRPC_ENDPOINT: [gRPC endpoint for Dapr communication - should be set by scaffold]
    DAPR_HTTP_ENDPOINT: [HTTP endpoint for Dapr communication - should be set by scaffold]
    STORAGE_ACCOUNT_NAME: [Name of the Azure storage account]
    STORAGE_ACCOUNT_KEY: [Access key for the Azure storage account]
    CONTAINER_NAME: [Name of the container in Azure storage]
  workDir: upload
  command: ["python", "app.py"]
appLogDestination: ""
```

With the scaffold created, you can run the demo with diagrid dev start. First ensure that you have a Python environment. Install the following packages:

```bash
cloudevents==1.10.1
dapr==1.11.0
fastapi==0.111.0
grpcio==1.62.1
pydantic==2.4.2
requests==2.32.0
uvicorn==0.23.2
aiohttp==3.10.2
azure-ai-documentintelligence==1.0.0b3
azure-core==1.30.2
azure-storage-blob==12.22.0
groq==0.11.0
```

You can install the packages with the following command:

```bash
pip install -r requirements.txt
```

## Run with Dapr

To run with Dapr, add a dapr.yaml file to the root of the project with the following content:

```yaml
version: 1
apps:
  - appID: process
    appDirPath: ./process
    appPort: 8001
    command: ["python", "app.py"]
    env:
      STORAGE_ACCOUNT_NAME: [Name of the Azure storage account]
      STORAGE_ACCOUNT_KEY: [Access key for the Azure storage account]
      CONTAINER_NAME: [Name of the container in Azure storage]
      DOCINT_KEY: [API key for Azure Document Intelligence service]
      DOCINT_URL: [Endpoint URL for Azure Document Intelligence service]
      OPENAI_KEY: [API key for OpenAI service]
      AZURE_OPENAI_KEY: [API key for Azure OpenAI service]
      AZURE_OPENAI_ENDPOINT: [Endpoint URL for Azure OpenAI service]
      AZURE_OPENAI_MODEL: [Name of the Azure OpenAI model to use]
      AZURE_OPENAI_API_VERSION: [API version for Azure OpenAI service]
      INVOICE_EXTRACTOR_TYPE: [Type of invoice extractor to use (e.g., 'openai')]
      INVOICE_OUTPUT_HANDLER: [Type of output handler for invoice data (e.g., 'json')]
      GROQ_API_KEY: [API key for Groq service]
      KVSTORE_NAME: statestore
      PUBSUB_NAME: pubsub
  - appID: upload
    appDirPath: ./upload
    appPort: 8000
    command: ["python", "app.py"]
    env:
      STORAGE_ACCOUNT_NAME: [Name of the Azure storage account]
      STORAGE_ACCOUNT_KEY: [Access key for the Azure storage account]
      CONTAINER_NAME: [Name of the container in Azure storage]
      PUBSUB_NAME: pubsub
      KVSTORE_NAME: statestore
```

To run the app with Dapr, make sure Dapr is installed and Docker is running with Redis. The default statestore and pubsub names use Redis. Run the app with `dapr run -f .`