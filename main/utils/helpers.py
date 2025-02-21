from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def set_nested_value(container, keys, value):
    """Helper function for nested data structure"""
    # Your existing set_nested_value function

def get_calendar_weeks(current_date):
    """
    Generate a list of week objects for the specified month
    """
    # Get first and last day of the month
    first_day = current_date.replace(day=1)
    if current_date.month == 12:
        next_month = current_date.replace(year=current_date.year + 1, month=1, day=1)
    else:
        next_month = current_date.replace(month=current_date.month + 1, day=1)
    last_day = next_month - timedelta(days=1)
    
    # Find the start of the first week (Sunday)
    week_start = first_day - timedelta(days=first_day.weekday())
    
    weeks = []
    current_week = week_start
    
    # Keep adding weeks until we've covered the entire month
    while current_week <= last_day:
        week_end = current_week + timedelta(days=6)
        
        # Only include weeks that overlap with the current month
        if (week_end >= first_day or current_week <= last_day):
            weeks.append({
                'id': current_week.strftime('%Y-%m-%d'),
                'start': current_week,
                'end': week_end,
                'month': current_date.month  # Add month info for filtering
            })
        
        current_week += timedelta(days=7)
    
    logger.info(f"Generated weeks for {current_date.strftime('%Y-%m')}:")
    for week in weeks:
        logger.info(f"Week: {week['start'].strftime('%Y-%m-%d')} to {week['end'].strftime('%Y-%m-%d')}")
    
    return weeks
