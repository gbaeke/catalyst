from .base_cracker import BaseCracker
from .document_intelligence_cracker import DocumentIntelligenceCracker
import os

class CrackerFactory:
    @staticmethod
    def get_cracker(cracker_type: str = None) -> BaseCracker:
        if cracker_type is None:
            cracker_type = os.getenv('CRACKER_TYPE', 'document_intelligence')

        if cracker_type.lower() == 'document_intelligence':
            return DocumentIntelligenceCracker()
        # Add more crackers here as needed
        else:
            raise ValueError(f"Unsupported cracker type: {cracker_type}")