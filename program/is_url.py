"""
RinBot v1.4.3
feita por rin
"""

# Imports
import urllib.parse

# Verifica se uma string é uma URL válida ou não
def is_url(str):
    try:
        result = urllib.parse.urlparse(str)
        return all([result.scheme, result.netloc])
    except:
        return False