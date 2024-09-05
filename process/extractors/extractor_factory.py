from .base_extractor import BaseInvoiceExtractor
from .openai_extractor import OpenAIInvoiceExtractor
from .groq_extractor import GroqInvoiceExtractor
import os

class InvoiceExtractorFactory:
    @staticmethod
    def get_extractor(extractor_type: str = None) -> BaseInvoiceExtractor:
        if extractor_type is None:
            extractor_type = os.getenv('INVOICE_EXTRACTOR_TYPE', 'openai')

        if extractor_type.lower() == 'openai':
            return OpenAIInvoiceExtractor()
        elif extractor_type.lower() == 'groq':
            return GroqInvoiceExtractor()
        # Add more extractors here as needed
        else:
            raise ValueError(f"Unsupported extractor type: {extractor_type}")