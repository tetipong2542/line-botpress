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


def validate_recurring_day(freq, day_of_week=None, day_of_month=None):
    """
    Validate day based on recurring frequency

    Args:
        freq: Frequency type ('daily', 'weekly', 'monthly')
        day_of_week: Day of week (0-6, Monday=0) for weekly
        day_of_month: Day of month (1-31) for monthly

    Raises:
        ValueError: If day doesn't match frequency requirements

    Returns:
        tuple: (validated day_of_week, validated day_of_month)
    """
    freq = validate_frequency(freq)

    if freq == 'daily':
        # Daily doesn't need day specification
        return None, None

    elif freq == 'weekly':
        if day_of_week is None:
            raise ValueError("day_of_week is required for weekly frequency")
        try:
            day_of_week = int(day_of_week)
            if not (0 <= day_of_week <= 6):
                raise ValueError("day_of_week must be between 0 (Monday) and 6 (Sunday)")
            return day_of_week, None
        except (ValueError, TypeError):
            raise ValueError("Invalid day_of_week format")

    elif freq == 'monthly':
        if day_of_month is None:
            raise ValueError("day_of_month is required for monthly frequency")
        try:
            day_of_month = int(day_of_month)
            if not (1 <= day_of_month <= 31):
                raise ValueError("day_of_month must be between 1 and 31")
            return None, day_of_month
        except (ValueError, TypeError):
            raise ValueError("Invalid day_of_month format")

    return None, None


def validate_date_not_past(date_value, allow_today=True):
    """
    Validate that date is not in the past

    Args:
        date_value: Date string (ISO format) or datetime object
        allow_today: Whether today's date is allowed (default: True)

    Raises:
        ValueError: If date is in the past

    Returns:
        datetime: Validated datetime object
    """
    if isinstance(date_value, str):
        date_value = validate_date(date_value)

    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day)

    if allow_today:
        if date_value < today_start:
            raise ValueError("Date cannot be in the past")
    else:
        if date_value <= now:
            raise ValueError("Date must be in the future")

    return date_value


def validate_category_name(name):
    """
    Validate category name

    Args:
        name: Category name string

    Raises:
        ValueError: If name is invalid

    Returns:
        str: Validated and sanitized name
    """
    if not name or not name.strip():
        raise ValueError("Category name is required")

    name = sanitize_string(name, max_length=100)

    if not name:
        raise ValueError("Category name cannot be empty")

    if len(name) < 2:
        raise ValueError("Category name must be at least 2 characters")

    return name


def validate_email(email):
    """
    Validate email format

    Args:
        email: Email address string

    Raises:
        ValueError: If email format is invalid

    Returns:
        str: Validated email
    """
    if not email or not email.strip():
        raise ValueError("Email is required")

    email = email.strip().lower()

    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(pattern, email):
        raise ValueError("Invalid email format")

    return email


def validate_color_hex(color):
    """
    Validate hex color code

    Args:
        color: Hex color string (e.g., '#FF5733' or 'FF5733')

    Raises:
        ValueError: If color format is invalid

    Returns:
        str: Validated hex color with # prefix
    """
    if not color:
        return None

    color = color.strip()

    # Add # prefix if missing
    if not color.startswith('#'):
        color = '#' + color

    # Validate hex format
    pattern = r'^#[0-9A-Fa-f]{6}$'

    if not re.match(pattern, color):
        raise ValueError("Invalid color format. Use hex format like #FF5733")

    return color.upper()
