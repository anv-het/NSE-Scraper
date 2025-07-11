from typing import Dict, Any, Optional
from datetime import datetime
from Constant.http import HTTP_STATUS, HTTP_MESSAGES, RESPONSE_TYPES

def create_response(
    success: bool,
    data: Any = None,
    message: str = None,
    status_code: int = None,
    errors: list = None,
    metadata: Dict = None
) -> Dict:
    """
    Create standardized API response
    
    Args:
        success: Whether the operation was successful
        data: Response data
        message: Response message
        status_code: HTTP status code
        errors: List of error messages
        metadata: Additional metadata
    
    Returns:
        Standardized response dictionary
    """
    
    # Set default status code based on success
    if status_code is None:
        status_code = HTTP_STATUS.OK if success else HTTP_STATUS.INTERNAL_SERVER_ERROR
    
    # Set default message based on success and status code
    if message is None:
        if success:
            message = HTTP_MESSAGES.SUCCESS
        else:
            message = HTTP_MESSAGES.INTERNAL_SERVER_ERROR
    
    # Determine response type
    response_type = RESPONSE_TYPES.SUCCESS if success else RESPONSE_TYPES.ERROR
    
    response = {
        "success": success,
        "status_code": status_code,
        "message": message,
        "type": response_type,
        "timestamp": datetime.now().isoformat(),
        "data": data
    }
    
    # Add errors if provided
    if errors:
        response["errors"] = errors
    
    # Add metadata if provided
    if metadata:
        response["metadata"] = metadata
    
    return response

def success_response(
    data: Any = None,
    message: str = HTTP_MESSAGES.SUCCESS,
    status_code: int = HTTP_STATUS.OK,
    metadata: Dict = None
) -> Dict:
    """
    Create success response
    
    Args:
        data: Response data
        message: Success message
        status_code: HTTP status code
        metadata: Additional metadata
    
    Returns:
        Success response dictionary
    """
    return create_response(
        success=True,
        data=data,
        message=message,
        status_code=status_code,
        metadata=metadata
    )

def error_response(
    message: str = HTTP_MESSAGES.INTERNAL_SERVER_ERROR,
    status_code: int = HTTP_STATUS.INTERNAL_SERVER_ERROR,
    errors: list = None,
    data: Any = None,
    metadata: Dict = None
) -> Dict:
    """
    Create error response
    
    Args:
        message: Error message
        status_code: HTTP status code
        errors: List of error messages
        data: Any relevant data
        metadata: Additional metadata
    
    Returns:
        Error response dictionary
    """
    return create_response(
        success=False,
        data=data,
        message=message,
        status_code=status_code,
        errors=errors,
        metadata=metadata
    )

def validation_error_response(
    errors: list,
    message: str = HTTP_MESSAGES.UNPROCESSABLE_ENTITY,
    data: Any = None
) -> Dict:
    """
    Create validation error response
    
    Args:
        errors: List of validation errors
        message: Error message
        data: Any relevant data
    
    Returns:
        Validation error response dictionary
    """
    return create_response(
        success=False,
        data=data,
        message=message,
        status_code=HTTP_STATUS.UNPROCESSABLE_ENTITY,
        errors=errors
    )

def not_found_response(
    message: str = HTTP_MESSAGES.NOT_FOUND,
    resource: str = None
) -> Dict:
    """
    Create not found response
    
    Args:
        message: Error message
        resource: Resource that was not found
    
    Returns:
        Not found response dictionary
    """
    if resource:
        message = f"{resource} not found"
    
    return create_response(
        success=False,
        message=message,
        status_code=HTTP_STATUS.NOT_FOUND
    )

def unauthorized_response(
    message: str = HTTP_MESSAGES.UNAUTHORIZED
) -> Dict:
    """
    Create unauthorized response
    
    Args:
        message: Error message
    
    Returns:
        Unauthorized response dictionary
    """
    return create_response(
        success=False,
        message=message,
        status_code=HTTP_STATUS.UNAUTHORIZED
    )

def forbidden_response(
    message: str = HTTP_MESSAGES.FORBIDDEN
) -> Dict:
    """
    Create forbidden response
    
    Args:
        message: Error message
    
    Returns:
        Forbidden response dictionary
    """
    return create_response(
        success=False,
        message=message,
        status_code=HTTP_STATUS.FORBIDDEN
    )

def too_many_requests_response(
    message: str = HTTP_MESSAGES.TOO_MANY_REQUESTS,
    retry_after: int = None
) -> Dict:
    """
    Create too many requests response
    
    Args:
        message: Error message
        retry_after: Seconds to wait before retrying
    
    Returns:
        Too many requests response dictionary
    """
    metadata = {}
    if retry_after:
        metadata["retry_after"] = retry_after
    
    return create_response(
        success=False,
        message=message,
        status_code=HTTP_STATUS.TOO_MANY_REQUESTS,
        metadata=metadata if metadata else None
    )

def service_unavailable_response(
    message: str = HTTP_MESSAGES.SERVICE_UNAVAILABLE
) -> Dict:
    """
    Create service unavailable response
    
    Args:
        message: Error message
    
    Returns:
        Service unavailable response dictionary
    """
    return create_response(
        success=False,
        message=message,
        status_code=HTTP_STATUS.SERVICE_UNAVAILABLE
    )

def paginated_response(
    data: list,
    page: int,
    per_page: int,
    total: int,
    message: str = HTTP_MESSAGES.SUCCESS
) -> Dict:
    """
    Create paginated response
    
    Args:
        data: List of data items
        page: Current page number
        per_page: Number of items per page
        total: Total number of items
        message: Response message
    
    Returns:
        Paginated response dictionary
    """
    total_pages = (total + per_page - 1) // per_page
    
    metadata = {
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }
    
    return create_response(
        success=True,
        data=data,
        message=message,
        metadata=metadata
    )

def scraping_response(
    success: bool,
    scraped_count: int = 0,
    data_type: str = None,
    source: str = "NSE",
    data: Any = None,
    errors: list = None
) -> Dict:
    """
    Create response for scraping operations
    
    Args:
        success: Whether scraping was successful
        scraped_count: Number of items scraped
        data_type: Type of data scraped
        source: Data source
        data: Scraped data
        errors: Any errors encountered
    
    Returns:
        Scraping response dictionary
    """
    if success:
        message = f"Successfully scraped {scraped_count} {data_type or 'items'} from {source}"
        status_code = HTTP_STATUS.OK
    else:
        message = f"Failed to scrape {data_type or 'data'} from {source}"
        status_code = HTTP_STATUS.INTERNAL_SERVER_ERROR
    
    metadata = {
        "scraping": {
            "source": source,
            "data_type": data_type,
            "scraped_count": scraped_count,
            "timestamp": datetime.now().isoformat()
        }
    }
    
    return create_response(
        success=success,
        data=data,
        message=message,
        status_code=status_code,
        errors=errors,
        metadata=metadata
    )

def create_success_response(
    data: Any = None,
    message: str = HTTP_MESSAGES.SUCCESS,
    status_code: int = HTTP_STATUS.OK,
    metadata: Dict = None
) -> Dict:
    """
    Create success response (alias for success_response)
    
    Args:
        data: Response data
        message: Success message
        status_code: HTTP status code
        metadata: Additional metadata
    
    Returns:
        Success response dictionary
    """
    return success_response(data, message, status_code, metadata)
