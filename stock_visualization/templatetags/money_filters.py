from django import template
from decimal import Decimal

register = template.Library()

@register.filter(name='money')
def money_format(value):
    """
    Format a value as currency with proper digit separators
    Example: 1234567.89 -> $1,234,567.89
    """
    if value is None:
        return "$0.00"
    
    try:
        # Convert to float or decimal if it's a string
        if isinstance(value, str):
            value = Decimal(value)
        
        # Format with thousand separators and 2 decimal places
        return "${:,.2f}".format(value)
    except (ValueError, TypeError):
        return "$0.00"

@register.filter(name='percentage')
def percentage_format(value):
    """
    Format a value as percentage with proper digit separators
    Example: 12.34 -> 12.34%
    """
    if value is None:
        return "0.00%"
    
    try:
        # Convert to float if it's a string
        if isinstance(value, str):
            value = float(value)
        
        # Format with 2 decimal places and a percent sign
        return "{:,.2f}%".format(value)
    except (ValueError, TypeError):
        return "0.00%"
