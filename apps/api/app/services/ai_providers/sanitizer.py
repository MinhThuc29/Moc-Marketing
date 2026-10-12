import re

# Regex phát hiện số điện thoại Việt Nam (03x, 05x, 07x, 08x, 09x, hoặc +84)
VIETNAM_PHONE_REGEX = re.compile(r"(?:\+84|0)(?:3[2-9]|5[25689]|7[06-9]|8[1-9]|9[0-9])\d{7}\b")
GENERIC_PHONE_REGEX = re.compile(r"\b0\d{9}\b")

# Regex phát hiện địa chỉ email
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

# Regex phát hiện số CMND / CCCD (9 hoặc 12 chữ số đứng độc lập)
ID_CARD_REGEX = re.compile(r"\b\d{9}\b|\b\d{12}\b")


def mask_pii(text: str) -> str:
    """
    Loại bỏ hoặc che giấu thông tin định danh cá nhân (PII) trước khi gửi tới AI Provider:
    - Số điện thoại -> [SĐT_ĐÃ_ẨN]
    - Email -> [EMAIL_ĐÃ_ẨN]
    - CCCD / CMND -> [ID_ĐÃ_ẨN]
    """
    if not text:
        return ""

    sanitized = text
    # 1. Che giấu email
    sanitized = EMAIL_REGEX.sub("[EMAIL_ĐÃ_ẨN]", sanitized)

    # 2. Che giấu số điện thoại
    sanitized = VIETNAM_PHONE_REGEX.sub("[SĐT_ĐÃ_ẨN]", sanitized)
    sanitized = GENERIC_PHONE_REGEX.sub("[SĐT_ĐÃ_ẨN]", sanitized)

    # 3. Che giấu CCCD / CMND
    sanitized = ID_CARD_REGEX.sub("[ID_ĐÃ_ẨN]", sanitized)

    return sanitized
