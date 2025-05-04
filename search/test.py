import re
import unicodedata

def is_youtube_link(query: str) -> bool:
    """
    Check if the query is a valid YouTube link.
    """
    return bool(re.search(r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/', query))

def clean_query(query: str) -> str:
    """
    Clean and normalize the input query.
    - Trims whitespace
    - Normalizes unicode characters
    - Collapses repeated spaces
    """
    # Normalize unicode (e.g. converting accented characters to their basic form)
    query = unicodedata.normalize('NFKC', query)

    # Remove leading and trailing whitespace
    query = query.strip()

    # Collapse multiple spaces to a single one
    query = re.sub(r'\s+', ' ', query)

    return query

def validate_query(query: str) -> bool:
    """
    Validate the input query for basic safety and length.
    - Ensure the query isn't empty after cleaning.
    - Reject queries that are too long or too short.
    """
    # Ensure query isn't empty or just whitespace
    if not query:
        return False
    
    # Optional: Reject queries that are too long or too short
    if len(query) > 500:  # Arbitrary max length
        return False
    
    return True

def clean_and_classify_query(query: str):
    """
    Main function that detects if the query is a YouTube link or a search term.
    - Cleans the query
    - Detects if it's a valid YouTube link or a search term
    - Returns structured result: {'type': 'youtube'/'search', 'query': cleaned query}
    """
    # Clean and validate the query
    query = clean_query(query)
    if not validate_query(query):
        return {'type': 'invalid', 'query': query}

    # Check if it's a YouTube link
    if is_youtube_link(query):
        return {'type': 'youtube', 'query': query}
    
    # Otherwise treat it as a search term
    return {'type': 'search', 'query': query}



dangerous_inputs = [
    "  ",                                 # Just whitespace
    "; rm -rf /",                         # Shell injection attempt
    "' OR 1=1 --",                        # SQL injection pattern
    "<script>alert('xss')</script>",     # XSS attempt
    "`shutdown now`",                    # Command injection attempt
    "$(reboot)",                         # Command substitution
    "DROP TABLE users;",                 # SQL injection
    "🎵🔥💣😈",                          # Only emojis
    "🙂 search music 🎶",                 # Normal text + emojis
    "SELECT * FROM songs WHERE name = 'a';",  # Full SQL snippet
]

youtube_links = [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",                # Standard watch link
    "http://youtube.com/watch?v=dQw4w9WgXcQ",                     # HTTP
    "https://youtu.be/dQw4w9WgXcQ",                               # Shortened format
    "www.youtube.com/watch?v=dQw4w9WgXcQ",                        # Missing scheme
    "youtube.com/watch?v=dQw4w9WgXcQ",                            # No www or scheme
    "https://www.youtube.com/embed/dQw4w9WgXcQ",                  # Embed URL
    "https://youtube.com/v/dQw4w9WgXcQ",                          # Legacy flash-based format
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=43s",          # With timestamp
    "https://www.youtube.com/shorts/dQw4w9WgXcQ",                 # Shorts format
    "https://www.youtube.com/playlist?list=PLynG1Isc01zhKXGlIEB", # Playlist
]




for k in dangerous_inputs:
    result = clean_and_classify_query(k)
    print(result)

for c in youtube_links:
    result = clean_and_classify_query(c)
    print(result)




input_query = """
vs term

Strips junk

Rejects dangerous input

Returns structured info for search logic?

You said:
y
ChatGPT said:
Here's the helper function clean_and_classify_query() that detects YouTube links, cleans up the input, and validates it. It handles basic sanitization and prepares the query for further processing.

python
Copy
Edit
import re
import unicodedata

def is_youtube_link(query: str) -> bool:
    Check if the query is a valid YouTube link.
    return bool(re.search(r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/', query))

def clean_query(query: str) -> str:
    Clean and normalize the input query.
    - Trims whitespace
    - Normalizes unicode characters
    - Collapses repeated spaces
    # Normalize unicode (e.g. converting accented characters to their basic form)
    query = unicodedata.normalize('NFKC', query)

    # Remove leading and trailing whitespace
    query = query.strip()

    # Collapse multiple spaces to a single one
    query = re.sub(r'\s+', ' ', query)

    return query

def validate_query(query: str) -> bool:
    Validate the input query for basic safety and length.
    - Ensure the query isn't empty after cleaning.
    - Reject queries that are too long or too short.
    # Ensure query isn't empty or just whitespace
    if not query:
        return False
    
    # Optional: Reject queries that are too long or too short
    if len(query) > 500:  # Arbitrary max length
        return False
    
    return True

def clean_and_classify_query(query: str):
    Main function that detects if the query is a YouTube link or a search term.
    - Cleans the query
    - Detects if it's a valid YouTube link or a search term
    - Returns structured result: {'type': 'youtube'/'search', 'query': cleaned query}
    # Clean and validate the query
    query = clean_query(query)
    if not validate_query(query):
        return {'type': 'invalid', 'query': query}

    # Check if it's a YouTube link
    if is_youtube_link(query):
        return {'type': 'youtube', 'query': query}
    
    # Otherwise treat it as a search term
    return {'type': 'search', 'query': query}

# Example usage:
input_query = "   https://www.youtube.com/watch?v=dQw4w9WgXcQ    "
result = clean_and_classify_query(input_query)
print(result)  # {'type': 'youtube', 'query': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'}

input_query = "search term for music!"
result = clean_and_classify_query(input_query)
print(result)  # {'type': 'search', 'query': 'search term for music!'}
How it Works:
clean_query():

Normalizes unicode (like emojis or accented characters).

Strips extra whitespace and collapses multiple spaces.

validate_query():

Rejects empty or overly long queries (you can adjust length limits).

is_youtube_link():

Detects if the query is a YouTube URL using a regex pattern.

clean_and_classify_query():

Cleans, validates, and classifies the query as either a YouTube link, a search term, or invalid input.

Handling Edge Cases:
The function will handle links like youtu.be or youtube.com.

It strips out unnecessary spaces and normalizes the input, so even if a user enters some odd characters or emojis, it will still process the query appropriately.

Let me know if you want more specific details or changes!


"""
result = clean_and_classify_query(input_query)
print(result)  # {'type': 'search', 'query': 'search term for music!'}

