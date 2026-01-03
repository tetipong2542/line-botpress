"""
Helper utilities
"""
import secrets
import string
from datetime import datetime


def generate_id(prefix='id'):
    """
    Generate a unique ID with prefix

    Args:
        prefix: Prefix for the ID (e.g., 'usr', 'prj', 'txn')

    Returns:
        Unique ID string
    """
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    random_suffix = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8))
    return f"{prefix}_{timestamp}_{random_suffix}"


def generate_short_code(length=8):
    """
    Generate a short alphanumeric code

    Args:
        length: Length of the code

    Returns:
        Alphanumeric code
    """
    alphabet = string.ascii_lowercase + string.digits
    # Exclude similar looking characters
    alphabet = alphabet.replace('0', '').replace('o', '').replace('1', '').replace('l', '')
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def satang_to_baht(satang):
    """
    Convert satang (cents) to baht (dollars)

    Args:
        satang: Amount in satang

    Returns:
        Amount in baht (float)
    """
    return satang / 100.0


def baht_to_satang(baht):
    """
    Convert baht to satang

    Args:
        baht: Amount in baht (float or int)

    Returns:
        Amount in satang (int)
    """
    return int(baht * 100)


def format_currency(amount, currency='THB'):
    """
    Format amount as currency string

    Args:
        amount: Amount in satang
        currency: Currency code

    Returns:
        Formatted currency string
    """
    baht = satang_to_baht(amount)
    if currency == 'THB':
        return f"฿{baht:,.2f}"
    return f"{baht:,.2f} {currency}"
