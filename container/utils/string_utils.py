

def get_text_after_separator(response: str, separator: str) -> tuple[str, str]:
    return response.split(separator)[1], response.split(separator)[0]