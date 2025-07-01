from werkzeug.datastructures import FileStorage 
from libs.google_vertex import add_corpus, add_file
from services.handle_agent import get_agent_by_id, update_agent
from typing import List
"""
Each agent has a rag corpus_id
when user upload a file, it will be uploaded to the rag corpus_id
if the agent does not have a rag corpus_id, it will be created
"""
def handle_upload_file(files: List[FileStorage], agent_id: str) -> str:
    agent = get_agent_by_id(agent_id)
    if not agent:
        raise Exception("Agent not found")
    if not agent["corpus_id"]:
        rag_corpus = add_corpus()
        corpus_id = rag_corpus.name.split("/")[-1]
        agent["corpus_id"] = corpus_id
        update_agent(agent_id, corpus_id=corpus_id)
    for file in files:
        add_file(file, agent["corpus_id"])
    return f"File '{files[0].filename}' uploaded successfully to RagCorpus '{agent['corpus_id']}'."