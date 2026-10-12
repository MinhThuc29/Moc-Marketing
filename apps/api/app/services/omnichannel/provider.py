import csv
import io
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any


def parse_datetime(dt_str: str) -> datetime:
    """Helper to parse common Vietnamese & ISO datetime formats"""
    dt_str = dt_str.strip()
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d",
        "%d/%m/%Y",
    ]
    for fmt in formats:
        try:
            parsed = datetime.strptime(dt_str, fmt)
            if not parsed.tzinfo:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
        except ValueError:
            continue
    return datetime.now(timezone.utc)


def parse_currency(val: Any) -> float:
    """Helper to parse numbers formatted as currency (e.g. '120.000', '120,000', '120000 VND')"""
    if val is None or val == "":
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().replace("VND", "").replace("đ", "").replace("Đ", "").strip()
    # Check if format uses dot as thousands separator (e.g. 120.000)
    if "." in s and "," not in s:
        # If dot is used as decimal or thousand
        parts = s.split(".")
        if len(parts[-1]) == 3:  # likely thousand separator like 120.000
            s = s.replace(".", "")
    elif "," in s and "." not in s:
        parts = s.split(",")
        if len(parts[-1]) == 3:  # 120,000
            s = s.replace(",", "")
        else:
            s = s.replace(",", ".")
    elif "," in s and "." in s:
        # e.g. 120,000.00
        s = s.replace(",", "")
    try:
        return float(re.sub(r"[^\d.-]", "", s))
    except ValueError:
        return 0.0


@dataclass
class NormalizedItem:
    product_name: str
    product_sku: str
    product_unit: str
    quantity: int
    unit_price: float
    total_price: float
    note: Optional[str] = None


@dataclass
class NormalizedOrderRow:
    external_order_id: str
    channel: str
    customer_name: str
    customer_phone: str
    delivery_address: str
    gross_amount: float
    merchant_discount: float
    platform_fee: float
    other_fee: float
    net_amount: float
    ordered_at: datetime
    items: List[NormalizedItem] = field(default_factory=list)
    customer_note: Optional[str] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class BaseMarketplaceProvider(ABC):
    @abstractmethod
    def parse_file_content(self, content: str, filename: str) -> List[NormalizedOrderRow]:
        pass

    def validate_connection(self) -> bool:
        return True


class GrabOrderProvider(BaseMarketplaceProvider):
    """
    Parser for GrabFood Merchant sales & settlement report exports.
    Handles columns such as:
    Order ID / Mã đơn hàng, Order Time / Thời gian, Customer / Khách hàng,
    Gross Sales / Tổng tiền món, Merchant Discount / Khuyến mãi quán,
    Commission / Chiết khấu Grab, Net Payout / Thực nhận quán, Items / Danh sách món.
    """

    def parse_file_content(self, content: str, filename: str) -> List[NormalizedOrderRow]:
        rows: List[NormalizedOrderRow] = []
        reader = csv.DictReader(io.StringIO(content))
        if not reader.fieldnames:
            return rows

        field_map = {f.strip().lower(): f for f in reader.fieldnames}

        def get_val(row_dict: dict, *candidates) -> str:
            for cand in candidates:
                cand_lower = cand.lower()
                for key_lower, orig_key in field_map.items():
                    if cand_lower in key_lower:
                        val = row_dict.get(orig_key, "")
                        if val is not None and str(val).strip() != "":
                            return str(val).strip()
            return ""

        for idx, r in enumerate(reader, start=1):
            order_id = get_val(r, "order id", "mã đơn", "order_id", "booking code", "short_order_number")
            if not order_id:
                order_id = f"GRAB-{idx:04d}"

            time_str = get_val(r, "order time", "thời gian", "date", "created_at", "ngày đặt", "time")
            ordered_at = parse_datetime(time_str) if time_str else datetime.now(timezone.utc)

            customer = get_val(r, "customer", "khách hàng", "tên khách", "recipient", "consumer_name") or "Khách hàng GrabFood"
            phone = get_val(r, "phone", "sđt", "số điện thoại", "telephone") or "0900000000"
            address = get_val(r, "address", "địa chỉ", "delivery_address") or "Giao qua tài xế GrabExpress"

            gross = parse_currency(get_val(r, "gross", "tổng tiền", "tổng giá trị", "subtotal", "food_price", "item_total"))
            discount = parse_currency(get_val(r, "merchant discount", "khuyến mãi quán", "quán giảm", "merchant_promo"))
            fee = parse_currency(get_val(r, "commission", "chiết khấu grab", "phí grab", "platform_fee", "grab_fee"))
            other = parse_currency(get_val(r, "other fee", "phí khác", "tax", "thuế"))
            net = parse_currency(get_val(r, "net", "thực nhận", "net payout", "settlement"))

            # Fallback calculations if net is not present or fee is zero
            if gross <= 0:
                gross = 100000.0  # reasonable default if row is minimally specified
            if fee <= 0 and gross > 0:
                fee = round(gross * 0.20, 0)  # Standard 20% GrabFood platform commission
            if net <= 0:
                net = max(0.0, gross - discount - fee - other)

            # Parse items summary if available
            items_str = get_val(r, "items", "món", "chi tiết món", "order items", "description")
            items: List[NormalizedItem] = []
            if items_str:
                parts = items_str.split(";") if ";" in items_str else items_str.split(",")
                for p in parts:
                    p = p.strip()
                    if not p:
                        continue
                    qty = 1
                    match_qty = re.search(r"x\s*(\d+)", p) or re.search(r"(\d+)\s*x", p)
                    if match_qty:
                        qty = int(match_qty.group(1))
                    name = re.sub(r"x\s*\d+|\d+\s*x", "", p).strip() or p
                    items.append(
                        NormalizedItem(
                            product_name=name,
                            product_sku="GRAB-ITEM",
                            product_unit="Phần",
                            quantity=qty,
                            unit_price=round(gross / max(1, qty), 0),
                            total_price=gross,
                        )
                    )
            else:
                items.append(
                    NormalizedItem(
                        product_name="Combo Món Healthy (GrabFood)",
                        product_sku="GRAB-COMBO",
                        product_unit="Phần",
                        quantity=1,
                        unit_price=gross,
                        total_price=gross,
                    )
                )

            rows.append(
                NormalizedOrderRow(
                    external_order_id=order_id,
                    channel="GRAB",
                    customer_name=customer,
                    customer_phone=phone,
                    delivery_address=address,
                    gross_amount=gross,
                    merchant_discount=discount,
                    platform_fee=fee,
                    other_fee=other,
                    net_amount=net,
                    ordered_at=ordered_at,
                    items=items,
                    customer_note=get_val(r, "note", "ghi chú"),
                    raw_data=r,
                )
            )

        return rows


class ShopeeFoodOrderProvider(BaseMarketplaceProvider):
    """
    Parser for ShopeeFood Merchant order & settlement reports.
    Handles columns such as:
    Shopee Order ID / Mã đơn Shopee, Order Time / Thời gian tạo,
    Customer / Người nhận, Subtotal / Tạm tính,
    Merchant Discount / Giảm giá quán, Service Fee / Phí dịch vụ Shopee (25%),
    Net Settlement / Quyết toán.
    """

    def parse_file_content(self, content: str, filename: str) -> List[NormalizedOrderRow]:
        rows: List[NormalizedOrderRow] = []
        reader = csv.DictReader(io.StringIO(content))
        if not reader.fieldnames:
            return rows

        field_map = {f.strip().lower(): f for f in reader.fieldnames}

        def get_val(row_dict: dict, *candidates) -> str:
            for cand in candidates:
                cand_lower = cand.lower()
                for key_lower, orig_key in field_map.items():
                    if cand_lower in key_lower:
                        val = row_dict.get(orig_key, "")
                        if val is not None and str(val).strip() != "":
                            return str(val).strip()
            return ""

        for idx, r in enumerate(reader, start=1):
            order_id = get_val(r, "shopee order id", "mã đơn shopee", "order id", "partner_order_id", "tracking_code")
            if not order_id:
                order_id = f"SPF-{idx:04d}"

            time_str = get_val(r, "order time", "thời gian", "date", "created_at", "ngày đặt")
            ordered_at = parse_datetime(time_str) if time_str else datetime.now(timezone.utc)

            customer = get_val(r, "customer", "người nhận", "tên khách", "buyer") or "Khách hàng ShopeeFood"
            phone = get_val(r, "phone", "sđt", "số điện thoại") or "0911000000"
            address = get_val(r, "address", "địa chỉ", "delivery_address") or "Giao qua tài xế ShopeeFood"

            gross = parse_currency(get_val(r, "subtotal", "tạm tính", "tổng giá trị", "gross", "item_amount"))
            discount = parse_currency(get_val(r, "merchant discount", "giảm giá quán", "voucher quán"))
            fee = parse_currency(get_val(r, "service fee", "phí dịch vụ", "chiết khấu shopee", "commission", "platform_fee"))
            other = parse_currency(get_val(r, "other", "phí khác", "tax"))
            net = parse_currency(get_val(r, "net settlement", "quyết toán", "thực nhận", "net"))

            if gross <= 0:
                gross = 120000.0
            if fee <= 0 and gross > 0:
                fee = round(gross * 0.25, 0)  # Standard 25% ShopeeFood service fee
            if net <= 0:
                net = max(0.0, gross - discount - fee - other)

            items_str = get_val(r, "items", "món", "chi tiết món", "product_name")
            items: List[NormalizedItem] = []
            if items_str:
                parts = items_str.split(";") if ";" in items_str else items_str.split(",")
                for p in parts:
                    p = p.strip()
                    if not p:
                        continue
                    qty = 1
                    match_qty = re.search(r"x\s*(\d+)", p) or re.search(r"(\d+)\s*x", p)
                    if match_qty:
                        qty = int(match_qty.group(1))
                    name = re.sub(r"x\s*\d+|\d+\s*x", "", p).strip() or p
                    items.append(
                        NormalizedItem(
                            product_name=name,
                            product_sku="SPF-ITEM",
                            product_unit="Phần",
                            quantity=qty,
                            unit_price=round(gross / max(1, qty), 0),
                            total_price=gross,
                        )
                    )
            else:
                items.append(
                    NormalizedItem(
                        product_name="Món Ăn Healthy (ShopeeFood)",
                        product_sku="SPF-DEFAULT",
                        product_unit="Phần",
                        quantity=1,
                        unit_price=gross,
                        total_price=gross,
                    )
                )

            rows.append(
                NormalizedOrderRow(
                    external_order_id=order_id,
                    channel="SHOPEEFOOD",
                    customer_name=customer,
                    customer_phone=phone,
                    delivery_address=address,
                    gross_amount=gross,
                    merchant_discount=discount,
                    platform_fee=fee,
                    other_fee=other,
                    net_amount=net,
                    ordered_at=ordered_at,
                    items=items,
                    customer_note=get_val(r, "note", "ghi chú"),
                    raw_data=r,
                )
            )

        return rows


class ManualImportProvider(BaseMarketplaceProvider):
    """
    Universal CSV parser for manual omnichannel order imports.
    """

    def parse_file_content(self, content: str, filename: str) -> List[NormalizedOrderRow]:
        rows: List[NormalizedOrderRow] = []
        reader = csv.DictReader(io.StringIO(content))
        if not reader.fieldnames:
            return rows

        field_map = {f.strip().lower(): f for f in reader.fieldnames}

        def get_val(row_dict: dict, *candidates) -> str:
            for cand in candidates:
                cand_lower = cand.lower()
                for key_lower, orig_key in field_map.items():
                    if cand_lower in key_lower:
                        val = row_dict.get(orig_key, "")
                        if val is not None and str(val).strip() != "":
                            return str(val).strip()
            return ""

        for idx, r in enumerate(reader, start=1):
            channel = (get_val(r, "channel", "kênh", "source") or "MANUAL").upper()
            order_id = get_val(r, "order_id", "external_id", "mã đơn", "id") or f"{channel}-{idx:04d}"
            time_str = get_val(r, "ordered_at", "thời gian", "date", "created_at")
            ordered_at = parse_datetime(time_str) if time_str else datetime.now(timezone.utc)

            customer = get_val(r, "customer_name", "khách hàng", "customer") or "Khách hàng"
            phone = get_val(r, "phone", "sđt") or "0900000000"
            address = get_val(r, "address", "địa chỉ") or "Tại quầy / Trực tiếp"

            gross = parse_currency(get_val(r, "gross_amount", "gross", "tổng tiền"))
            discount = parse_currency(get_val(r, "merchant_discount", "giảm giá", "discount"))
            fee = parse_currency(get_val(r, "platform_fee", "phí sàn", "fee"))
            other = parse_currency(get_val(r, "other_fee", "phí khác"))
            net = parse_currency(get_val(r, "net_amount", "thực nhận", "net"))

            if net <= 0 and gross > 0:
                net = max(0.0, gross - discount - fee - other)

            items_str = get_val(r, "items", "sản phẩm")
            items = [
                NormalizedItem(
                    product_name=items_str or f"Đơn hàng {channel}",
                    product_sku=f"{channel}-ITEM",
                    product_unit="Phần",
                    quantity=1,
                    unit_price=gross,
                    total_price=gross,
                )
            ]

            rows.append(
                NormalizedOrderRow(
                    external_order_id=order_id,
                    channel=channel,
                    customer_name=customer,
                    customer_phone=phone,
                    delivery_address=address,
                    gross_amount=gross,
                    merchant_discount=discount,
                    platform_fee=fee,
                    other_fee=other,
                    net_amount=net,
                    ordered_at=ordered_at,
                    items=items,
                    customer_note=get_val(r, "note", "ghi chú"),
                    raw_data=r,
                )
            )

        return rows


def get_order_provider(channel: str) -> BaseMarketplaceProvider:
    channel_upper = channel.strip().upper()
    if channel_upper == "GRAB":
        return GrabOrderProvider()
    elif channel_upper == "SHOPEEFOOD":
        return ShopeeFoodOrderProvider()
    else:
        return ManualImportProvider()
