"""
RinBot v1.4.3 (GitHub release)
made by rin
"""

# Imports
import urllib.parse

# Checks if a string is a valid URL
def is_url(str):
    try:
        result = urllib.parse.urlparse(str)
        return all([result.scheme, result.netloc])
    except:
        return False