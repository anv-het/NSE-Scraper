# HTTP status codes and related constants

# Success status codes
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_202_ACCEPTED = 202
HTTP_204_NO_CONTENT = 204

# Client error status codes
HTTP_400_BAD_REQUEST = 400
HTTP_401_UNAUTHORIZED = 401
HTTP_403_FORBIDDEN = 403
HTTP_404_NOT_FOUND = 404
HTTP_405_METHOD_NOT_ALLOWED = 405
HTTP_409_CONFLICT = 409
HTTP_422_UNPROCESSABLE_ENTITY = 422
HTTP_429_TOO_MANY_REQUESTS = 429

# Server error status codes
HTTP_500_INTERNAL_SERVER_ERROR = 500
HTTP_502_BAD_GATEWAY = 502
HTTP_503_SERVICE_UNAVAILABLE = 503
HTTP_504_GATEWAY_TIMEOUT = 504

# HTTP status messages
HTTP_STATUS_MESSAGES = {
    200: "OK",
    201: "Created",
    202: "Accepted",
    204: "No Content",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    409: "Conflict",
    422: "Unprocessable Entity",
    429: "Too Many Requests",
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout"
}

# HTTP methods
HTTP_GET = "GET"
HTTP_POST = "POST"
HTTP_PUT = "PUT"
HTTP_DELETE = "DELETE"
HTTP_PATCH = "PATCH"
HTTP_OPTIONS = "OPTIONS"
HTTP_HEAD = "HEAD"

# Content types
CONTENT_TYPE_JSON = "application/json"
CONTENT_TYPE_FORM = "application/x-www-form-urlencoded"
CONTENT_TYPE_MULTIPART = "multipart/form-data"
CONTENT_TYPE_TEXT = "text/plain"
CONTENT_TYPE_HTML = "text/html"
CONTENT_TYPE_XML = "application/xml"

# Common headers
HEADER_AUTHORIZATION = "Authorization"
HEADER_CONTENT_TYPE = "Content-Type"
HEADER_ACCEPT = "Accept"
HEADER_USER_AGENT = "User-Agent"
HEADER_REFERER = "Referer"
HEADER_ORIGIN = "Origin"
HEADER_X_FORWARDED_FOR = "X-Forwarded-For"
HEADER_X_REAL_IP = "X-Real-IP"

# CORS headers
HEADER_ACCESS_CONTROL_ALLOW_ORIGIN = "Access-Control-Allow-Origin"
HEADER_ACCESS_CONTROL_ALLOW_METHODS = "Access-Control-Allow-Methods"
HEADER_ACCESS_CONTROL_ALLOW_HEADERS = "Access-Control-Allow-Headers"
HEADER_ACCESS_CONTROL_ALLOW_CREDENTIALS = "Access-Control-Allow-Credentials"

# Cache control headers
HEADER_CACHE_CONTROL = "Cache-Control"
HEADER_EXPIRES = "Expires"
HEADER_ETAG = "ETag"
HEADER_LAST_MODIFIED = "Last-Modified"

# Security headers
HEADER_X_CONTENT_TYPE_OPTIONS = "X-Content-Type-Options"
HEADER_X_FRAME_OPTIONS = "X-Frame-Options"
HEADER_X_XSS_PROTECTION = "X-XSS-Protection"
HEADER_STRICT_TRANSPORT_SECURITY = "Strict-Transport-Security"

# API response codes for business logic
API_SUCCESS = 1000
API_ERROR = 1001
API_VALIDATION_ERROR = 1002
API_UNAUTHORIZED = 1003
API_FORBIDDEN = 1004
API_NOT_FOUND = 1005
API_RATE_LIMITED = 1006
API_SERVICE_UNAVAILABLE = 1007

# API response messages
API_RESPONSE_MESSAGES = {
    API_SUCCESS: "Operation completed successfully",
    API_ERROR: "An error occurred while processing the request",
    API_VALIDATION_ERROR: "Invalid input data provided",
    API_UNAUTHORIZED: "Authentication required",
    API_FORBIDDEN: "Access denied",
    API_NOT_FOUND: "Requested resource not found",
    API_RATE_LIMITED: "Request rate limit exceeded",
    API_SERVICE_UNAVAILABLE: "Service temporarily unavailable"
}

# Timeout values (in seconds)
DEFAULT_REQUEST_TIMEOUT = 30
SHORT_TIMEOUT = 10
LONG_TIMEOUT = 60
FILE_UPLOAD_TIMEOUT = 300

# Request retry configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1  # seconds
EXPONENTIAL_BACKOFF_MULTIPLIER = 2

# Response formats
RESPONSE_FORMAT_JSON = "json"
RESPONSE_FORMAT_XML = "xml"
RESPONSE_FORMAT_CSV = "csv"
RESPONSE_FORMAT_HTML = "html"

# Common user agents
USER_AGENT_CHROME = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
USER_AGENT_FIREFOX = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
USER_AGENT_SAFARI = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15"
USER_AGENT_EDGE = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"

# HTTP error categories
CLIENT_ERROR_CODES = range(400, 500)
SERVER_ERROR_CODES = range(500, 600)
SUCCESS_CODES = range(200, 300)
REDIRECT_CODES = range(300, 400)




# HTTP status codes and messages for NSE Scraper application

class HTTP_STATUS:
    # Success responses
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204
    
    # Redirection
    MOVED_PERMANENTLY = 301
    FOUND = 302
    NOT_MODIFIED = 304
    
    # Client errors
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    NOT_ACCEPTABLE = 406
    REQUEST_TIMEOUT = 408
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    TOO_MANY_REQUESTS = 429
    
    # Server errors
    INTERNAL_SERVER_ERROR = 500
    NOT_IMPLEMENTED = 501
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504

class HTTP_MESSAGES:
    # Success messages
    SUCCESS = "Request successful"
    CREATED = "Resource created successfully"
    UPDATED = "Resource updated successfully"
    DELETED = "Resource deleted successfully"
    
    # Error messages
    BAD_REQUEST = "Bad request. Please check your request parameters"
    UNAUTHORIZED = "Unauthorized. Invalid or missing authentication token"
    FORBIDDEN = "Forbidden. You don't have permission to access this resource"
    NOT_FOUND = "Resource not found"
    METHOD_NOT_ALLOWED = "Method not allowed"
    UNPROCESSABLE_ENTITY = "Unprocessable entity. Please check your request data"
    TOO_MANY_REQUESTS = "Too many requests. Please try again later"
    
    INTERNAL_SERVER_ERROR = "Internal server error. Please try again later"
    SERVICE_UNAVAILABLE = "Service temporarily unavailable. Please try again later"
    
    # NSE specific messages
    NSE_CONNECTION_ERROR = "Failed to connect to NSE website"
    NSE_DATA_ERROR = "Failed to retrieve data from NSE"
    NSE_PARSING_ERROR = "Failed to parse NSE response"
    NSE_TIMEOUT_ERROR = "Request to NSE timed out"
    
    # Database messages
    DATABASE_ERROR = "Database operation failed"
    DATABASE_CONNECTION_ERROR = "Failed to connect to database"
    
    # Scraping messages
    SCRAPING_SUCCESS = "Data scraped successfully"
    SCRAPING_ERROR = "Failed to scrape data"
    
    # Token messages
    TOKEN_INVALID = "Invalid authentication token"
    TOKEN_EXPIRED = "Authentication token has expired"
    TOKEN_MISSING = "Authentication token is required"

class RESPONSE_TYPES:
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

# Standard response templates
STANDARD_RESPONSES = {
    HTTP_STATUS.OK: {
        "status_code": HTTP_STATUS.OK,
        "message": HTTP_MESSAGES.SUCCESS,
        "type": RESPONSE_TYPES.SUCCESS
    },
    HTTP_STATUS.CREATED: {
        "status_code": HTTP_STATUS.CREATED,
        "message": HTTP_MESSAGES.CREATED,
        "type": RESPONSE_TYPES.SUCCESS
    },
    HTTP_STATUS.BAD_REQUEST: {
        "status_code": HTTP_STATUS.BAD_REQUEST,
        "message": HTTP_MESSAGES.BAD_REQUEST,
        "type": RESPONSE_TYPES.ERROR
    },
    HTTP_STATUS.UNAUTHORIZED: {
        "status_code": HTTP_STATUS.UNAUTHORIZED,
        "message": HTTP_MESSAGES.UNAUTHORIZED,
        "type": RESPONSE_TYPES.ERROR
    },
    HTTP_STATUS.FORBIDDEN: {
        "status_code": HTTP_STATUS.FORBIDDEN,
        "message": HTTP_MESSAGES.FORBIDDEN,
        "type": RESPONSE_TYPES.ERROR
    },
    HTTP_STATUS.NOT_FOUND: {
        "status_code": HTTP_STATUS.NOT_FOUND,
        "message": HTTP_MESSAGES.NOT_FOUND,
        "type": RESPONSE_TYPES.ERROR
    },
    HTTP_STATUS.UNPROCESSABLE_ENTITY: {
        "status_code": HTTP_STATUS.UNPROCESSABLE_ENTITY,
        "message": HTTP_MESSAGES.UNPROCESSABLE_ENTITY,
        "type": RESPONSE_TYPES.ERROR
    },
    HTTP_STATUS.TOO_MANY_REQUESTS: {
        "status_code": HTTP_STATUS.TOO_MANY_REQUESTS,
        "message": HTTP_MESSAGES.TOO_MANY_REQUESTS,
        "type": RESPONSE_TYPES.WARNING
    },
    HTTP_STATUS.INTERNAL_SERVER_ERROR: {
        "status_code": HTTP_STATUS.INTERNAL_SERVER_ERROR,
        "message": HTTP_MESSAGES.INTERNAL_SERVER_ERROR,
        "type": RESPONSE_TYPES.ERROR
    },
    HTTP_STATUS.SERVICE_UNAVAILABLE: {
        "status_code": HTTP_STATUS.SERVICE_UNAVAILABLE,
        "message": HTTP_MESSAGES.SERVICE_UNAVAILABLE,
        "type": RESPONSE_TYPES.ERROR
    }
}

# Content types
CONTENT_TYPES = {
    'JSON': 'application/json',
    'XML': 'application/xml',
    'HTML': 'text/html',
    'TEXT': 'text/plain',
    'CSV': 'text/csv',
    'FORM': 'application/x-www-form-urlencoded',
    'MULTIPART': 'multipart/form-data'
}
