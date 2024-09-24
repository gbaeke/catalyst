import os
from pydantic import BaseModel, Field, field_validator, ValidationError

# there are other ways to work with settings and Pydantic or settings management packages
# this is a simple way to define settings for the app

class Settings(BaseModel):
    dapr_http_port: str = Field(default_factory=lambda: os.getenv('DAPR_HTTP_PORT', '3500'))
    dapr_http_endpoint: str = Field(default_factory=lambda: os.getenv('DAPR_HTTP_ENDPOINT', 'http://localhost'))
    dapr_api_token: str = Field(default_factory=lambda: os.getenv('DAPR_API_TOKEN', ''))
    pubsub_name: str = Field(default_factory=lambda: os.getenv('PUBSUB_NAME', 'pubsub'))
    storage_account_name: str = Field(default_factory=lambda: os.getenv('STORAGE_ACCOUNT_NAME', ''))
    storage_account_key: str = Field(default_factory=lambda: os.getenv('STORAGE_ACCOUNT_KEY', ''))
    container_name: str = Field(default_factory=lambda: os.getenv('CONTAINER_NAME', ''))
    docint_key: str = Field(default_factory=lambda: os.getenv('DOCINT_KEY', ''))
    docint_url: str = Field(default_factory=lambda: os.getenv('DOCINT_URL', ''))
    kvstore_name: str = Field(default_factory=lambda: os.getenv('KVSTORE_NAME', 'kvstore'))
    invoke_target_appid: str = Field(default_factory=lambda: os.getenv('INVOKE_APPID', 'upload'))
    azure_openai_key: str = Field(default_factory=lambda: os.getenv('AZURE_OPENAI_KEY', ''))
    azure_openai_endpoint: str = Field(default_factory=lambda: os.getenv('AZURE_OPENAI_ENDPOINT', ''))
    azure_openai_model: str = Field(default_factory=lambda: os.getenv('AZURE_OPENAI_MODEL', ''))
    azure_openai_api_version: str = Field(default_factory=lambda: os.getenv('AZURE_OPENAI_API_VERSION', ''))
    pusher_app_id: str = Field(default_factory=lambda: os.getenv('PUSHER_APP_ID', ''))
    pusher_key: str = Field(default_factory=lambda: os.getenv('PUSHER_KEY', ''))
    pusher_secret: str = Field(default_factory=lambda: os.getenv('PUSHER_SECRET', ''))
    pusher_cluster: str = Field(default_factory=lambda: os.getenv('PUSHER_CLUSTER', 'eu'))
    pusher_channel: str = Field(default_factory=lambda: os.getenv('PUSHER_CHANNEL', 'docproc'))
    extractor_type: str = Field(default_factory=lambda: os.getenv('INVOICE_EXTRACTOR_TYPE', 'openai'))
    output_handler_types: list[str] = Field(default_factory=lambda: os.getenv('INVOICE_OUTPUT_HANDLER', 'pusher').split(','))
    event_grid_topic_endpoint: str = Field(default_factory=lambda: os.getenv('EVENT_GRID_TOPIC_ENDPOINT', ''))
    event_grid_topic_key: str = Field(default_factory=lambda: os.getenv('EVENT_GRID_TOPIC_KEY', ''))
    cracker_type: str = Field(default_factory=lambda: os.getenv('CRACKER_TYPE', 'document_intelligence'))

    @field_validator('pubsub_name', 'kvstore_name', 'storage_account_name', 'storage_account_key', 'container_name', mode='before')
    def check_required_variables(cls, v, field):
        if not v:
            raise ValueError(f'{field.name} must be set')
        return v


    @field_validator('docint_key', 'docint_url', mode='before')
    def check_docint_variables(cls, v, values):
        if values.get('cracker_type') == 'document_intelligence' and not v:
            raise ValueError('docint_key and docint_url must be set when cracker_type is "document_intelligence"')
        return v

    @field_validator('azure_openai_key', 'azure_openai_endpoint', 'azure_openai_model', 'azure_openai_api_version', mode='before')
    def check_azure_openai_variables(cls, v, values):
        if values.get('extractor_type') == 'openai' and not v:
            raise ValueError('All Azure OpenAI variables must be set when extractor_type is "openai"')
        return v

    @field_validator('pusher_app_id', 'pusher_key', 'pusher_secret', 'pusher_cluster', 'pusher_channel', mode='before')
    def check_pusher_variables(cls, v, values):
        if 'pusher' in values.get('output_handler_types', []) and not v:
            raise ValueError('All Pusher variables must be set when "pusher" is in output_handler_types')
        return v

    @field_validator('event_grid_topic_endpoint', 'event_grid_topic_key', mode='before')
    def check_event_grid_variables(cls, v, values):
        if 'event_grid' in values.get('output_handler_types', []) and not v:
            raise ValueError('event_grid_topic_endpoint and event_grid_topic_key must be set when "event_grid" is in output_handler_types')
        return v

settings = Settings()