from .base_extractor import BaseExtractor
from .openai_extractor import OpenAIExtractor
from .groq_extractor import GroqExtractor
from .ollama_extractor import OllamaExtractor  # Import the new extractor
import os

class ExtractorFactory:
    @staticmethod
    def get_extractor(extractor_type: str = None) -> BaseExtractor:
        if extractor_type is None:
            extractor_type = os.getenv('EXTRACTOR_TYPE', 'openai')

        if extractor_type.lower() == 'openai':
            return OpenAIExtractor()
        elif extractor_type.lower() == 'groq':
            return GroqExtractor()
        elif extractor_type.lower() == 'ollama':  # Add the new extractor type
            return OllamaExtractor()
        # Add more extractors here as needed
        else:
            raise ValueError(f"Unsupported extractor type: {extractor_type}")