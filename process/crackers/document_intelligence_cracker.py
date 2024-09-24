from .base_cracker import BaseCracker
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult, AnalyzeDocumentRequest
from azure.core.credentials import AzureKeyCredential
import logging
from config import settings

class DocumentIntelligenceCracker(BaseCracker):
    def __init__(self):
        self.client = DocumentIntelligenceClient(
            endpoint=settings.docint_url, credential=AzureKeyCredential(settings.docint_key)
        )

    def crack(self, file_content: bytes) -> str:
        try:
            doc_request = AnalyzeDocumentRequest(bytes_source=file_content)
            poller = self.client.begin_analyze_document("prebuilt-layout", doc_request)
            logging.info("Document Intelligence processing started.")
            result: AnalyzeResult = poller.result(timeout=10)
            logging.info("Document Intelligence processing completed successfully.")
            
            lines = [line.content for page in result.pages for line in page.lines]
            return "\n".join(lines)
        except Exception as e:
            logging.error(f"Could not extract text from document: {str(e)}")
            raise