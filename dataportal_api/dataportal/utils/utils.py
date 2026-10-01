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


def split_comma_values(value):
    """Split one value or a list of values on commas. Repeated query params stay separate."""
    if not value:
        return []
    items = value if isinstance(value, list) else [value]
    names = []
    for item in items:
        names.extend(part.strip() for part in unquote(str(item)).split(",") if part.strip())
    return names
