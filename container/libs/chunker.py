from typing import List, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv


load_dotenv()

# Initialize OpenAI embeddings with proper configuration
embed_model = OpenAIEmbeddings(
    model="text-embedding-3-small"  # Using the latest embedding model
)

# Semantic Chunking
def semantic_chunk_text(
    text: str,
    separators: Optional[List[str]] = None
) -> List[Document]:
    """
    Split text into semantically meaningful chunks using LangChain's RecursiveCharacterTextSplitter.
    
    Args:
        text (str): The input text to be chunked
        separators (List[str], optional): List of separators to use for splitting text. 
            If None, uses default separators: ["\n\n", "\n", " ", ""]
    
    Returns:
        List[Document]: A list of Document objects containing the chunked text
    """
    if separators is None:
        separators = ["\n\n", "\n", " ", ""]
    
#     class langchain_experimental.text_splitter.SemanticChunker(
# embeddings: Embeddings,
# buffer_size: int = 1,
# add_start_index: bool = False,
# breakpoint_threshold_type: Literal['percentile', 'standard_deviation', 'interquartile', 'gradient'] = 'percentile',
# breakpoint_threshold_amount: float | None = None,
# number_of_chunks: int | None = None,
# sentence_split_regex: str = '(?<=[.?!])\\s+',
# min_chunk_size: int | None = None,
# )
    # Initialize the text splitter
    text_splitter = SemanticChunker(
        embeddings=embed_model,
        buffer_size=1,
        add_start_index=False,
        breakpoint_threshold_type='percentile',
        breakpoint_threshold_amount=None,
        number_of_chunks=None,
        sentence_split_regex='(?<=[.?!])\\s+',
        min_chunk_size=None
    )
    
    # Split the text into chunks
    chunks = text_splitter.create_documents([text])
    
    return chunks

def semantic_chunk_documents(
    documents: List[Document],
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    separators: Optional[List[str]] = None
) -> List[Document]:
    """
    Split a list of documents into semantically meaningful chunks.
    
    Args:
        documents (List[Document]): List of Document objects to be chunked
        chunk_size (int, optional): The target size of each text chunk. Defaults to 1000.
        chunk_overlap (int, optional): The number of characters to overlap between chunks. Defaults to 200.
        separators (List[str], optional): List of separators to use for splitting text.
            If None, uses default separators: ["\n\n", "\n", " ", ""]
    
    Returns:
        List[Document]: A list of Document objects containing the chunked text
    """
    if separators is None:
        separators = ["\n\n", "\n", " ", ""]
    
    # Initialize the text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=separators,
        length_function=len,
        is_separator_regex=False
    )
    
    # Split the documents into chunks
    chunks = text_splitter.split_documents(documents)
    
    return chunks

# Example usage
if __name__ == "__main__":
    # Example text
    sample_text = """
    This is a sample text that will be split into chunks.
    The RecursiveCharacterTextSplitter will try to split on paragraphs first,
    then sentences, then words if necessary.
    
    It maintains semantic meaning by trying to keep related content together.
    This is particularly useful for processing large documents.
    """
    
    # Chunk the text
    chunks = semantic_chunk_text(sample_text, chunk_size=100, chunk_overlap=20)
    
    # Print the chunks
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i + 1}:")
        print(chunk.page_content)
        print("-" * 50)
