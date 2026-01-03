"""
Input validation utilities
"""
from datetime import datetime
import re


def validate_transaction_type(type_value):
    """Validate transaction type"""
    valid_types = ['income', 'expense']
    if type_value not in valid_types:
        raise ValueError(f"Invalid type. Must be one of: {', '.join(valid_types)}")
    return type_value


def validate_amount(amount):
    """Validate transaction amount"""
    try:
        amount_int = int(amount)
        if amount_int <= 0:
            raise ValueError("Amount must be greater than 0")
        return amount_int
    except (ValueError, TypeError):
        raise ValueError("Invalid amount format")


def validate_currency(currency):
    """Validate currency code"""
    valid_currencies = ['THB', 'USD', 'EUR', 'JPY']
    if currency not in valid_currencies:
        raise ValueError(f"Invalid currency. Must be one of: {', '.join(valid_currencies)}")
    return currency


def validate_month_yyyymm(month_str):
    """Validate month format YYYY-MM"""
    pattern = r'^\d{4}-\d{2}$'
    if not re.match(pattern, month_str):
        raise ValueError("Invalid month format. Must be YYYY-MM")

    # Validate actual date
    try:
        year, month = map(int, month_str.split('-'))
        if not (1 <= month <= 12):
            raise ValueError("Invalid month value")
        return month_str
    except ValueError:
        raise ValueError("Invalid month format")


def validate_frequency(freq):
    """Validate recurring frequency"""
    valid_frequencies = ['daily', 'weekly', 'monthly']
    if freq not in valid_frequencies:
        raise ValueError(f"Invalid frequency. Must be one of: {', '.join(valid_frequencies)}")
    return freq


def validate_role(role):
    """Validate user role"""
    valid_roles = ['owner', 'admin', 'member']
    if role not in valid_roles:
        raise ValueError(f"Invalid role. Must be one of: {', '.join(valid_roles)}")
    return role


def validate_insight_fields_level(level):
    """Validate insight fields level"""
    valid_levels = ['minimal', 'standard', 'full']
    if level not in valid_levels:
        raise ValueError(f"Invalid fields level. Must be one of: {', '.join(valid_levels)}")
    return level


def validate_date(date_str):
    """Validate date string (ISO format)"""
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        raise ValueError("Invalid date format. Use ISO 8601 format")


def sanitize_string(text, max_length=None):
    """Sanitize string input"""
    if text is None:
        return None

    text = str(text).strip()

    if max_length and len(text) > max_length:
        text = text[:max_length]

    return text if text else None
