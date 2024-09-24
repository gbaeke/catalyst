from .base_cracker import BaseCracker
from tika import parser

class TikaCracker(BaseCracker):
    def crack(self, file_content: bytes) -> str:
        try:
            parsed = parser.from_buffer(file_content)
        except Exception as e:
            return None
        
        return parsed["content"]
