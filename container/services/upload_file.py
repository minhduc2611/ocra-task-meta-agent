from libs.pdf_lib import process_pdf, read_pdf_from_buffer, allowed_file
from werkzeug.datastructures import FileStorage
from typing import List, Tuple, Dict, Any, Optional
from libs.weaviate_lib import upload_documents, search_non_vector_collection, insert_to_collection, COLLECTION_DOCUMENTS, update_collection_object, delete_collection_object, COLLECTION_FILES, client, delete_collection_objects_many, get_collection_count
from weaviate.collections.classes.filters import Filter
from weaviate.collections.classes.grpc import Sort
from datetime import datetime
from data_classes.common_classes import Document, File

def upload_file(files: List[FileStorage], description: str, author: str) -> Tuple[List[dict], int]:
    if not files:
        raise Exception("No files uploaded")

    results = []
    for file in files:
        if not allowed_file(file.filename):
            raise Exception(f"File type not allowed for {file.filename}. Only PDF files are accepted.")
        # Read PDF content from buffer
        pdf_content = read_pdf_from_buffer(file)
        
        # Process the PDF content
        chunks = process_pdf(
            text=pdf_content,
        )
        file_id = create_file(File(
            name=file.filename,
            path=file.filename,
            author=author
        ))
        if not file_id:
            raise Exception("Failed to create file")
        # Convert chunks to a serializable format
        serialized_chunks = [
            {
                "content": chunk.page_content,
                "title": file.filename,
                "file_id": file_id,
                "description": description,
                "author": author,
            }
            for chunk in chunks
        ]
        results.append({
            "filename": file.filename,
            "num_chunks": len(chunks),
            "chunks": serialized_chunks
        })
        
        failed_objects = upload_documents(serialized_chunks)

        return results, len(failed_objects)
    
    return results, 0

# manage files
def get_files(limit: int, offset: int) -> tuple[List[Dict[str, Any]], int]:
    """
    Get all files with pagination and total count
    """
    # Get files data
    files = search_non_vector_collection(
        collection_name=COLLECTION_FILES,
        limit=limit,    
        offset=offset,
        properties=["name", "path", "author", "created_at", "updated_at"],
        sort=Sort.by_property("created_at", ascending=True)
    )
    
    # Get total count
    total_count = get_collection_count(
        collection_name=COLLECTION_FILES
    )
    
    files = [File(**file) for file in files]
    return files, total_count

def create_file(file: File) -> str:
    """
    Create a new file
    """
    if not file.author:
        raise Exception("Author is required")
    
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    file_id = insert_to_collection(
        collection_name=COLLECTION_FILES,
        properties={
            "name": file.name,
            "path": file.path,
            "author": file.author,
            "created_at": now,
            "updated_at": now
        }
    )
    return file_id

def get_file_by_name(name: str) -> Optional[File]:
    """
    Get a file by its name
    """
    file = search_non_vector_collection(
        collection_name=COLLECTION_FILES,
        filters=Filter.by_property("name").equal(name),
        properties=["name", "path", "author", "created_at", "updated_at"],
        limit=1
    )
    if not file:
        raise Exception(f"File not found for name: {name}")
    return File(**file[0])

def get_file_by_id(file_id: str) -> File:
    """
    Get a file by its ID
    """
    file = search_non_vector_collection(
        collection_name=COLLECTION_FILES,
        filters=Filter.by_id().equal(file_id),
        properties=["name", "path", "author", "created_at", "updated_at"],
        limit=1
    )
    if not file:
        raise Exception(f"File not found for id: {file_id}")
    return File(**file[0])

def update_file(file_id: str, payload: File) -> File:
    """
    Update a file
    """
    file = get_file_by_id(file_id)
    if not file:
        raise Exception("File not found")
    
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    if payload.name:
        file.name = payload.name
    if payload.path:
        file.path = payload.path
    if payload.author:  
        file.author = payload.author
    
    update_file = {
        "name": file.name,
        "path": file.path,  
        "author": file.author,
        "updated_at": now
    }
    
    success = update_collection_object(
        collection_name=COLLECTION_FILES,
        uuid=file_id,
        properties=update_file
    )
    
    if not success:
        raise Exception("Failed to update file")
    
    return update_file

# def delete_file(file_id: str) -> bool:
#     """
#     Delete a file
#     """
#     # Check if file exists
#     file = get_file_by_id(file_id)
#     if not file:
#         raise Exception("File not found")
    
#     # Delete file   
#     success = delete_collection_object(
#         collection_name=COLLECTION_FILES,
#         uuid=file_id
#     )
    
#     if not success:
#         raise Exception("Failed to delete file")
    
#     return True

def delete_file_with_transaction(file_id: str) -> bool:
    """
    Delete a file and its associated documents in a transaction
    
    Args:
        file_id: ID of the file to delete
        
    Returns:
        True if deletion was successful
        
    Raises:
        Exception: If the transaction fails
    """
    try:
        # Get the file first
        file = get_file_by_id(file_id)
        if not file:
            raise Exception("File not found")
        
        
        # Delete all documents associated with this file
        delete_collection_objects_many(
            collection_name=COLLECTION_DOCUMENTS,
            filters=Filter.by_property("file_id").equal(file_id)
        )
        
        # Delete the file
        delete_collection_object(
            collection_name=COLLECTION_FILES,
            uuid=file_id
        )
        
        return True

    except Exception as e:
        raise Exception(f"Error in delete transaction: {str(e)}")

# Update the existing functions to use transactions where appropriate
def delete_file(file_id: str) -> bool:
    """Delete a file and its associated documents in a transaction"""
    return delete_file_with_transaction(file_id)

# manage documents 

def get_documents(limit: int, offset: int) -> tuple[List[Dict[str, Any]], int]:
    """
    Get all documents with pagination and total count
    
    Returns:
        Tuple of (documents, total_count)
    """
    try:
        # Get documents data
        documents = search_non_vector_collection(
            collection_name=COLLECTION_DOCUMENTS,
            limit=limit,
            offset=offset,
            properties=["title", "content", "description", "author", "created_at", "updated_at"],
            sort=Sort.by_property("created_at", ascending=True)
        )
        
        # Get total count
        total_count = get_collection_count(
            collection_name=COLLECTION_DOCUMENTS
        )
        
        return documents, total_count
    except Exception as e:
        raise Exception(f"Error getting documents: {str(e)}")

def get_document_by_id(document_id: str) -> Document:
    """
    Get a document by its ID
    
    Args:
        document_id: ID of the document to retrieve
        
    Returns:
        Document data if found, None otherwise
    """
    try:
        documents = search_non_vector_collection(
            collection_name=COLLECTION_DOCUMENTS,
            filters=Filter.by_id().equal(document_id),
            limit=1,
            properties=["title", "content", "description", "author", "created_at", "updated_at"]
        )
        
        if not documents:
            raise Exception(f"Document not found for id: {document_id}")
        
        document = documents[0]
        return {
            "uuid": document.uuid,
            "title": document.title,
            "content": document.content,
            "description": document.description,
            "author": document.author,
            "created_at": document.created_at,
            "updated_at": document.updated_at
        }
    except Exception as e:
        raise Exception(f"Error getting document: {str(e)}")

def create_document(document: Document) -> Document:
    """
    Create a new document
    
    Args:
        document: Document object to create
        
    Returns:
        Created document with ID
    """
    try:
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Prepare document properties
        properties = {
            "title": document.title,
            "content": document.content,
            "description": document.description,
            "author": document.author,
            "created_at": now,
            "updated_at": now
        }
        
        # Insert document and get UUID
        document_id = insert_to_collection(
            collection_name=COLLECTION_DOCUMENTS,
            properties=properties
        )
        
        if not document_id:
            raise Exception("Failed to create document")
            
        # Set the ID and return the document
        document.uuid = document_id
        return document
        
    except Exception as e:
        raise Exception(f"Error creating document: {str(e)}")

def update_document(document_id: str, payload: Document) -> Document:
    """
    Update an existing document
    
    Args:
        document_id: ID of the document to update
        document: Updated document data
        
    Returns:
        Updated document
    """
    try:
        # Check if document exists
        existing_docs = search_non_vector_collection(
            collection_name=COLLECTION_DOCUMENTS,
            filters=Filter.by_id().equal(document_id),
            properties=["title", "content", "description", "author", "created_at", "updated_at"],
            limit=1
        )
        new_document = Document(**existing_docs[0])
        if not existing_docs:
            raise Exception("Document not found")
        
        # Prepare update properties
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        if payload.title:
            new_document.title = payload.title
        if payload.content:
            new_document.content = payload.content
        if payload.description:
            new_document.description = payload.description
        if payload.author:
            new_document.author = payload.author
        
        update_document = {
            "title": new_document.title,
            "content": new_document.content,
            "description": new_document.description,
            "author": new_document.author,
            "created_at": new_document.created_at if new_document.created_at else now,
            "updated_at": now
        }
        
        # Update document
        success = update_collection_object(
            collection_name=COLLECTION_DOCUMENTS,
            uuid=document_id,
            properties=update_document
        )
        
        if not success:
            raise Exception("Failed to update document")

        return update_document
        
    except Exception as e:
        raise Exception(f"Error updating document: {str(e)}")

def delete_document(document_id: str) -> bool:
    """
    Delete a document
    
    Args:
        document_id: ID of the document to delete
        
    Returns:
        True if deletion was successful, False if document not found
    """
    try:
        # Check if document exists
        existing_docs = search_non_vector_collection(
            collection_name=COLLECTION_DOCUMENTS,
            filters=Filter.by_id().equal(document_id),
            limit=1
        )
        
        if not existing_docs:
            return False
            
        # Delete document
        success = delete_collection_object(
            collection_name=COLLECTION_DOCUMENTS,
            uuid=document_id
        )
        
        if not success:
            raise Exception("Failed to delete document")
            
        return True
        
    except Exception as e:
        raise Exception(f"Error deleting document: {str(e)}")

    