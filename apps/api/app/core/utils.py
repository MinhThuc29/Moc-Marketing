import re
import unicodedata


def slugify_vn(text: str) -> str:
    """
    Converts Vietnamese string into SEO-friendly URL slug.
    Example: 'Táo New Zealand giòn ngọt' -> 'tao-new-zealand-gion-ngot'
    """
    if not text:
        return ""

    # Normalize unicode
    text = unicodedata.normalize("NFKD", text)

    # Specific replacements for Vietnamese special vowels/consonants
    vn_map = {
        "đ": "d",
        "Đ": "d",
    }
    for k, v in vn_map.items():
        text = text.replace(k, v)

    # Strip diacritical marks
    text = "".join(c for c in text if not unicodedata.combining(c))

    # Convert to lowercase
    text = text.lower().strip()

    # Replace whitespace and punctuation with single hyphens
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)

    return text
