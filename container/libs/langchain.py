from langchain_openai import ChatOpenAI
from data_classes.common_classes import AgentProvider


def get_langchain_model(model: str, temperature: float = 0.7) -> ChatOpenAI:
    if model == "gpt-4o-mini":
        return ChatOpenAI(model="gpt-4o-mini", temperature=temperature)
    elif model == "gpt-3.5-turbo":
        return ChatOpenAI(model="gpt-3.5-turbo", temperature=temperature)
    else:
        raise ValueError(f"Model {model} not supported")
    
    
def check_model(model: str) -> AgentProvider:
    # include text gpt
    if model.find("gpt") != -1:
        return AgentProvider.OPENAI
    # include gemini
    elif model.find("gemini") != -1:
        return AgentProvider.GOOGLE_VERTEX
    elif model.find("fine_tuned_model") != -1: # fine-tuned model
        return AgentProvider.GOOGLE_VERTEX
    # include claude
    elif model.find("claude") != -1:
        return AgentProvider.ANTHROPIC
    # include deepseek
    elif model.find("deepseek") != -1:
        return AgentProvider.DEEPSEEK
    # include llama
    elif model.find("llama") != -1:
        return AgentProvider.LLAMA
    else:
        raise ValueError(f"Model {model} not supported")