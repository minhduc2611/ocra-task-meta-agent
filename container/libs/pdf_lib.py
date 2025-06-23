import os
from typing import List
from pypdf import PdfReader
from langchain.schema import Document
from libs.chunker import semantic_chunk_text


# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf'}
def read_pdf(file_path: str) -> str:
    """
    Read a PDF file and extract its text content.
    
    Args:
        file_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text from the PDF
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found at: {file_path}")
    
    # Initialize PDF reader
    reader = PdfReader(file_path)
    text = ""
    
    # Extract text from each page
    for page in reader.pages:
        text += page.extract_text() + "\n\n"
    
    return text

def process_pdf(
    text: str,
    output_file: str = None
) -> List[Document]:
    """
    Process text content and split it into semantic chunks.
    
    Args:
        text (str): Text content to process
        output_file (str, optional): Path to save the chunks. If None, chunks won't be saved.
        
    Returns:
        List[Document]: List of chunked documents
    """
    # Chunk the text
    print("Chunking text...")
    chunks = semantic_chunk_text(
        text,
    )
    
    # Save chunks to file if output_file is specified
    if output_file:
        print(f"Saving chunks to: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            for i, chunk in enumerate(chunks):
                f.write(f"\n{'='*50}\n")
                f.write(f"Chunk {i + 1}\n")
                f.write(f"{'='*50}\n\n")
                f.write(chunk.page_content)
                f.write("\n")
    
    return chunks
 
 
 
def allowed_file(filename: str) -> bool:
    """
    Check if the file extension is allowed.
    
    Args:
        filename (str): Name of the file to check
        
    Returns:
        bool: True if the file extension is allowed, False otherwise
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def read_pdf_from_buffer(file_buffer) -> str:
    """
    Read a PDF from a file buffer and extract its text content.
    
    Args:
        file_buffer: File buffer containing PDF data
        
    Returns:
        str: Extracted text from the PDF
    """
    # Initialize PDF reader with the buffer
    reader = PdfReader(file_buffer)
    text = ""
    
    # Extract text from each page
    for page in reader.pages:
        text += page.extract_text() + "\n\n"
    
    return text
