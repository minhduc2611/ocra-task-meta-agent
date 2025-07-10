from werkzeug.datastructures import FileStorage 
from libs.google_vertex import add_corpus, add_file
from services.handle_agent import get_agent_by_id, update_agent
from typing import List, Dict, Any, Generator
"""
Each agent has a rag corpus_id
when user upload a file, it will be uploaded to the rag corpus_id
if the agent does not have a rag corpus_id, it will be created
"""
def handle_upload_file(files: List[FileStorage], agent_id: str) -> Generator[Dict[str, Any], None, None]:
    agent = get_agent_by_id(agent_id)
    if not agent:
        yield {"error": "Agent not found", "status": "error"}
        return
    
    if not agent["corpus_id"]:
        yield {"status": "creating_corpus", "message": "Creating RAG corpus..."}
        rag_corpus = add_corpus()
        corpus_id = rag_corpus.name.split("/")[-1]
        agent["corpus_id"] = corpus_id
        update_agent(agent_id, corpus_id=corpus_id)
        yield {"status": "corpus_created", "corpus_id": corpus_id, "message": "RAG corpus created successfully"}
    
    total_files = len(files)
    successful_count = 0
    failed_count = 0
    
    yield {"status": "starting_upload", "total_files": total_files, "message": f"Starting upload of {total_files} files"}
    
    for index, file in enumerate(files, 1):
        try:
            yield {"status": "uploading", "filename": file.filename, "progress": f"{index}/{total_files}", "message": f"Uploading {file.filename}..."}
            
            #  ADD FILE TO RAG CORPUS
            add_file(file, agent["corpus_id"])
            successful_count += 1
            yield {
                "status": "success", 
                "filename": file.filename,
                "content_type": file.content_type,
                "size": file.content_length if hasattr(file, 'content_length') else None,
                "progress": f"{index}/{total_files}",
                "successful_count": successful_count,
                "failed_count": failed_count,
                "message": f"Successfully uploaded {file.filename}"
            }
        except Exception as e:
            failed_count += 1
            yield {
                "status": "failed",
                "filename": file.filename,
                "error": str(e),
                "progress": f"{index}/{total_files}",
                "successful_count": successful_count,
                "failed_count": failed_count,
                "message": f"Failed to upload {file.filename}: {str(e)}"
            }
    
    # Final summary
    yield {
        "status": "completed",
        "corpus_id": agent["corpus_id"],
        "total_files": total_files,
        "successful_count": successful_count,
        "failed_count": failed_count,
        "message": f"Upload completed. {successful_count} successful, {failed_count} failed"
    }
