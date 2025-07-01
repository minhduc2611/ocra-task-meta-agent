from pathlib import Path

def load_prompt_file(filepath: str) -> str:
    try:
        return Path(filepath).read_text(encoding='utf-8').strip()
    except FileNotFoundError:
        print(f"Prompt file {filepath} not found")
        return None
    except Exception as e:
        print(f"Error loading prompt file: {e}")
        return None