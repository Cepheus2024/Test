from app import create_app
from flask_wtf.csrf import CSRFProtect
from datetime import datetime

app = create_app()
csrf = CSRFProtect(app)  # Enable CSRF protection

# Add 'now' function to Jinja2 environment
app.jinja_env.globals['now'] = datetime.now

def safe_int_conversion(value):
    """Safely convert a string to an integer, handling invalid input."""
    if value.isdigit():
        return int(value)
    raise ValueError(f"Invalid input for integer conversion: '{value}'")

# Example usage (replace with actual logic where needed)
try:
    user_input = "42"  # Replace with actual input source
    number = safe_int_conversion(user_input)
    print(f"Converted number: {number}")
except ValueError as e:
    print(e)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
