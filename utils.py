"""
Utility functions for GeminiTask.
Handles Gemini API interactions and other helper functions.
"""

import datetime
import calendar
from dateutil import parser
import google.generativeai as genai
from config import get_api_key

def initialize_gemini():
    """Initialize the Gemini API client with the API key."""
    api_key = get_api_key()
    
    if not api_key:
        return False
    
    try:
        genai.configure(api_key=api_key)
        return True
    except Exception:
        return False


def extract_date_time(natural_language_date):
    """
    Extract structured date and time from natural language input using Gemini API.
    
    Args:
        natural_language_date (str): Natural language description of a date/time
        
    Returns:
        str: ISO 8601 formatted date-time string or None if parsing failed
    """
    if not natural_language_date:
        return None
        
    try:
        # Try to parse directly with dateutil first
        try:
            dt = parser.parse(natural_language_date, fuzzy=True)
            # If no time specified and parser.parse assigned 00:00:00,
            # assume end of day (23:59:59)
            if dt.hour == 0 and dt.minute == 0 and dt.second == 0:
                dt = dt.replace(hour=23, minute=59, second=59)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, parser.ParserError):
            # If direct parsing fails, use Gemini API
            pass
            
        # Check if Gemini API is available
        if not initialize_gemini():
            raise Exception("Gemini API not available. Please set your API key.")
            
        # Create a prompt for Gemini
        prompt = f"""
        Extract the exact date and time from the following text. 
        If no time is explicitly mentioned, assume the end of the day (23:59). 
        Return the result in ISO 8601 format (YYYY-MM-DD HH:MM:SS). 
        If no date or time is found, indicate with 'None'.
        
        Text: '{natural_language_date}'
        """
        
        # Generate response from Gemini
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        
        # Process the response
        response_text = response.text.strip()
        
        # Handle 'None' response
        if response_text == 'None':
            return None
            
        # Try to parse the returned date string
        try:
            dt = parser.parse(response_text)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, parser.ParserError):
            return None
            
    except Exception as e:
        print(f"Error processing date: {e}")
        return None


def suggest_due_date(task_description):
    """
    Suggest a due date based on the task description using Gemini API.
    
    Args:
        task_description (str): Description of the task
        
    Returns:
        str: Suggested due date in ISO 8601 format or None if suggestion failed
    """
    if not initialize_gemini():
        print("Gemini API not available. Please set your API key.")
        return None
        
    try:
        # Create a prompt for Gemini
        prompt = f"""
        Based on the following task description, suggest a realistic due date and time in ISO 8601 format (YYYY-MM-DD HH:MM:SS).
        If no specific timeframe is implied, suggest a reasonable default within the next week.
        Task: '{task_description}'
        """
        
        # Generate response from Gemini
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        
        # Process the response
        response_text = response.text.strip()
        
        # Try to parse the returned date string
        try:
            dt = parser.parse(response_text)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, parser.ParserError):
            return None
            
    except Exception as e:
        print(f"Error suggesting due date: {e}")
        return None


def suggest_context(task_description, previous_contexts):
    """
    Suggest a context based on the task description and previously used contexts.
    
    Args:
        task_description (str): Description of the task
        previous_contexts (list): List of previously used contexts
        
    Returns:
        str: Suggested context or 'general' if suggestion failed
    """
    if not previous_contexts:
        return "general"
        
    if not initialize_gemini():
        print("Gemini API not available. Please set your API key.")
        return "general"
        
    try:
        # Create a prompt for Gemini
        contexts_str = ", ".join([f"'{c}'" for c in previous_contexts])
        prompt = f"""
        Based on the task description '{task_description}' and the following list of previously used contexts: {contexts_str},
        suggest the most relevant context. If none seem relevant, suggest 'general'.
        """
        
        # Generate response from Gemini
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        
        # Process the response
        suggested_context = response.text.strip().lower()
        
        # Remove any quotes that might be in the response
        suggested_context = suggested_context.replace("'", "").replace('"', "")
        
        return suggested_context if suggested_context else "general"
            
    except Exception as e:
        print(f"Error suggesting context: {e}")
        return "general"


def format_relative_date(date_str):
    """
    Format a date in a user-friendly relative format.
    
    Args:
        date_str (str): ISO 8601 formatted date-time string
        
    Returns:
        str: User-friendly date string (e.g., "Today", "Tomorrow", "In 3 days", "2 days ago")
    """
    if not date_str:
        return "No due date"
        
    try:
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        now = datetime.datetime.now()
        
        # Calculate the difference in days
        delta = dt.date() - now.date()
        days_diff = delta.days
        
        if days_diff == 0:
            # Today
            hour_str = dt.strftime("%I:%M %p").lstrip("0")
            return f"Today at {hour_str}"
        elif days_diff == 1:
            # Tomorrow
            hour_str = dt.strftime("%I:%M %p").lstrip("0")
            return f"Tomorrow at {hour_str}"
        elif days_diff == -1:
            # Yesterday
            hour_str = dt.strftime("%I:%M %p").lstrip("0")
            return f"Yesterday at {hour_str}"
        elif 1 < days_diff < 7:
            # Within the next week
            day_name = dt.strftime("%A")
            hour_str = dt.strftime("%I:%M %p").lstrip("0")
            return f"{day_name} at {hour_str}"
        elif -7 < days_diff < 0:
            # Within the last week
            return f"{abs(days_diff)} days ago"
        else:
            # More than a week away or more than a week ago
            return dt.strftime("%b %d, %Y at %I:%M %p").lstrip("0").replace(" 0", " ")
            
    except (ValueError, TypeError):
        return "Invalid date"


def parse_date_range(date_range_str):
    """
    Parse a natural language date range into start and end dates.
    
    Args:
        date_range_str (str): Natural language date range (e.g., "next week", "this month")
        
    Returns:
        tuple: (start_date, end_date) in ISO 8601 format or (None, None) if parsing failed
    """
    common_ranges = {
        "today": (
            datetime.datetime.now().replace(hour=0, minute=0, second=0),
            datetime.datetime.now().replace(hour=23, minute=59, second=59)
        ),
        "tomorrow": (
            (datetime.datetime.now() + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0),
            (datetime.datetime.now() + datetime.timedelta(days=1)).replace(hour=23, minute=59, second=59)
        ),
        "yesterday": (
            (datetime.datetime.now() - datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0),
            (datetime.datetime.now() - datetime.timedelta(days=1)).replace(hour=23, minute=59, second=59)
        ),
        "this week": (
            (datetime.datetime.now() - datetime.timedelta(days=datetime.datetime.now().weekday())).replace(hour=0, minute=0, second=0),
            (datetime.datetime.now() + datetime.timedelta(days=6-datetime.datetime.now().weekday())).replace(hour=23, minute=59, second=59)
        ),
        "next week": (
            (datetime.datetime.now() + datetime.timedelta(days=7-datetime.datetime.now().weekday())).replace(hour=0, minute=0, second=0),
            (datetime.datetime.now() + datetime.timedelta(days=13-datetime.datetime.now().weekday())).replace(hour=23, minute=59, second=59)
        ),
        "this month": (
            datetime.datetime.now().replace(day=1, hour=0, minute=0, second=0),
            datetime.datetime.now().replace(day=calendar.monthrange(datetime.datetime.now().year, datetime.datetime.now().month)[1], hour=23, minute=59, second=59)
        ),
    }
    
    date_range_str = date_range_str.lower().strip()
    
    if date_range_str in common_ranges:
        start_date, end_date = common_ranges[date_range_str]
        return (start_date.strftime("%Y-%m-%d %H:%M:%S"), 
                end_date.strftime("%Y-%m-%d %H:%M:%S"))
    
    # For more complex ranges, use Gemini API
    try:
        if not initialize_gemini():
            print("Gemini API not available. Please set your API key.")
            return (None, None)
            
        # Create a prompt for Gemini
        prompt = f"""
        Parse the following date range expression into start and end dates.
        Return the results as a JSON object with 'start_date' and 'end_date' in ISO 8601 format (YYYY-MM-DD HH:MM:SS).
        If the range is open-ended, use None for the missing bound.
        
        Date range: '{date_range_str}'
        """
        
        # Generate response from Gemini
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        
        # Process the response
        import json
        try:
            date_range = json.loads(response.text)
            return (date_range.get("start_date"), date_range.get("end_date"))
        except json.JSONDecodeError:
            # Try to extract dates directly from the text
            lines = response.text.strip().split('\n')
            start_date = None
            end_date = None
            
            for line in lines:
                if "start_date" in line.lower():
                    parts = line.split(":", 1)
                    if len(parts) > 1:
                        start_date_str = parts[1].strip().strip('"\'').strip(',')
                        if start_date_str.lower() != "none":
                            start_date = parser.parse(start_date_str).strftime("%Y-%m-%d %H:%M:%S")
                
                if "end_date" in line.lower():
                    parts = line.split(":", 1)
                    if len(parts) > 1:
                        end_date_str = parts[1].strip().strip('"\'').strip(',')
                        if end_date_str.lower() != "none":
                            end_date = parser.parse(end_date_str).strftime("%Y-%m-%d %H:%M:%S")
            
            return (start_date, end_date)
            
    except Exception as e:
        print(f"Error parsing date range: {e}")
        return (None, None)
