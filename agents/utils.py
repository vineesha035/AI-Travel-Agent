def extract_text(content):
    """
    Some Gemini model versions return response.content as a plain string,
    others return a list of content blocks. Normalize both cases to a
    single clean string. Shared by any file that calls a Gemini LLM directly.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            block.get("text", "") for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    return str(content)