

def get_text_after_separator(response: str, separator: str) -> tuple[str, str]:
    if separator in response:
        return response.split(separator)[1], response.split(separator)[0]
    else:
        return response, ""