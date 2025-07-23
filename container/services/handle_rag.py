from werkzeug.datastructures import FileStorage 
from libs.google_vertex import add_file_async, upload_temp_file_async
from services.handle_agent import get_agent_by_id, update_agent
from typing import List, Dict, Any, AsyncGenerator
import asyncio
import tempfile
import os
from werkzeug.utils import secure_filename
from libs.google_vertex import add_corpus
"""
Each agent has a rag corpus_id
when user upload a file, it will be uploaded to the rag corpus_id
if the agent does not have a rag corpus_id, it will be created
"""

async def handle_upload_file(files: List[FileStorage], agent_id: str) -> AsyncGenerator[Dict[str, Any], None]:
    agent = get_agent_by_id(agent_id)
    if not agent:
        yield {"error": "Agent not found", "status": "error"}
        return
    
    if not agent["corpus_id"]:
        yield {"status": "creating_corpus", "message": "Creating RAG corpus..."}
        
        rag_corpus = add_corpus(display_name=agent["name"])
        corpus_id = rag_corpus.name.split("/")[-1]
        agent["corpus_id"] = corpus_id
        update_agent(agent_id, corpus_id=corpus_id)
        yield {"status": "corpus_created", "corpus_id": corpus_id, "message": "RAG corpus created successfully"}
    
    total_files = len(files)
    successful_count = 0
    failed_count = 0
    
    yield {"status": "starting_upload", "total_files": total_files, "message": f"Starting upload of {total_files} files"}
    
    # First, save all files to temporary locations to avoid file handle conflicts
    temp_files_data = []
    for index, file in enumerate(files, 1):
        yield {"status": "preparing", "filename": file.filename, "progress": f"{index}/{total_files}", "message": f"Preparing {file.filename}..."}
        
        # Save file to temporary location immediately
        
        if file.filename == '':
            failed_count += 1
            yield {
                "status": "failed",
                "filename": "unknown",
                "error": "File name is required",
                "progress": f"{index}/{total_files}",
                "successful_count": 0,
                "failed_count": failed_count,
                "message": "Failed: File name is required"
            }
            continue
            
        try:
            # Get the original filename and ensure it has an extension
            original_filename = file.filename or "uploaded_file"
            display_name = secure_filename(original_filename)
            
            # Extract file extension
            file_extension = ""
            if "." in original_filename:
                file_extension = "." + original_filename.split(".")[-1]
            
            # Create temporary file with proper extension
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)
            file.save(temp_file.name)
            temp_file.close()
            
            temp_files_data.append({
                'temp_path': temp_file.name,
                'display_name': display_name,
                'original_filename': original_filename,
                'content_type': file.content_type,
                'size': file.content_length if hasattr(file, 'content_length') else None,
                'index': index
            })
            
        except Exception as e:
            failed_count += 1
            yield {
                "status": "failed",
                "filename": file.filename,
                "error": str(e),
                "progress": f"{index}/{total_files}",
                "successful_count": 0,
                "failed_count": failed_count,
                "message": f"Failed to prepare {file.filename}: {str(e)}"
            }
    
    # Now create async tasks for all prepared files
    tasks = []
    task_to_metadata = {}
    
    for file_data in temp_files_data:
        index = file_data['index']
        yield {"status": "uploading", "filename": file_data['original_filename'], "progress": f"{index}/{total_files}", "message": f"Uploading {file_data['original_filename']}..."}
        
        # Create async task for this file using the temp path
        task = asyncio.create_task(upload_temp_file_async(file_data['temp_path'], file_data['display_name'], agent["corpus_id"]))
        tasks.append(task)
        task_to_metadata[task] = file_data
    
    # Process completed tasks as they finish
    pending_tasks = set(tasks)
    
    while pending_tasks:
        # Wait for at least one task to complete
        done, pending_tasks = await asyncio.wait(pending_tasks, return_when=asyncio.FIRST_COMPLETED)
        
        # Process all completed tasks
        for completed_task in done:
            file_data = task_to_metadata[completed_task]
            
            try:
                result = await completed_task
                successful_count += 1
                yield {
                    "status": "success", 
                    "filename": file_data['original_filename'],
                    "content_type": file_data['content_type'],
                    "size": file_data['size'],
                    "progress": f"{file_data['index']}/{total_files}",
                    "successful_count": successful_count,
                    "failed_count": failed_count,
                    "message": f"Successfully uploaded {file_data['original_filename']}",
                    "result": result
                }
            except Exception as e:
                failed_count += 1
                yield {
                    "status": "failed",
                    "filename": file_data['original_filename'],
                    "error": str(e),
                    "progress": f"{file_data['index']}/{total_files}",
                    "successful_count": successful_count,
                    "failed_count": failed_count,
                    "message": f"Failed to upload {file_data['original_filename']}: {str(e)}"
                }
            finally:
                # Clean up temporary file
                try:
                    if os.path.exists(file_data['temp_path']):
                        os.remove(file_data['temp_path'])
                except OSError as e:
                    print(f"Warning: Could not remove temporary file {file_data['temp_path']}: {e}")
    
    # Final summary
    yield {
        "status": "completed",
        "corpus_id": agent["corpus_id"],
        "total_files": total_files,
        "successful_count": successful_count,
        "failed_count": failed_count,
        "message": f"Upload completed. {successful_count} successful, {failed_count} failed"
    }
