import tika
from tika import parser

# Set the Tika server URL
tika.TikaClientOnly = True
tika.TikaServerEndpoint = 'http://localhost:9998/tika'

def extract_invoice_data(file_path: str) -> dict:
    """
    Extracts metadata and content from the given PDF file using Tika server.

    Args:
        file_path (str): Path to the PDF file.

    Returns:
        dict: A dictionary containing metadata and content.
    """
    parsed = parser.from_file(file_path)
    return {
        "metadata": parsed["metadata"],
        "content": parsed["content"]
    }

if __name__ == "__main__":
    file_path = 'invoice.pdf'
    data = extract_invoice_data(file_path)
    print("Metadata:", data["metadata"])
    print("Content:", data["content"])
