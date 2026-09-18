from urllib.parse import unquote


def convert_to_camel_case(text: str) -> str:
    """Convert a string to CamelCase."""
    return " ".join(word.capitalize() for word in text.split())


def split_comma_param(value):
    if not value:
        return []
    if isinstance(value, list):
        return value
    return [v.strip() for v in unquote(value).split(",")]
