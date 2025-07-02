import logging
import logging.handlers
import os
import json
from datetime import datetime
from flask import request, g
import functools

def _get_request_id():
    """Safely get request ID from Flask g object"""
    try:
        return getattr(g, 'request_id', None)
    except RuntimeError:
        return None

def _get_request_info():
    """Safely get request info from Flask request object"""
    try:
        if request:
            return {
                'method': request.method,
                'url': request.url,
                'remote_addr': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', '')
            }
    except RuntimeError:
        pass
    return None

class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add request context if available
        request_id = _get_request_id()
        if request_id:
            log_entry['request_id'] = request_id
        
        request_info = _get_request_info()
        if request_info:
            log_entry['request'] = request_info
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'extra'):
            log_entry.update(record.extra)
        
        return json.dumps(log_entry, ensure_ascii=False)

def setup_logging(app):
    """Configure logging for the Flask application"""
    
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(app.root_path, 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Configure root logger
    logging.getLogger().setLevel(logging.INFO)
    
    # Create formatters
    json_formatter = StructuredFormatter()
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # File handler for all logs
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(logs_dir, 'app.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(json_formatter)
    
    # Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        os.path.join(logs_dir, 'error.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(json_formatter)
    
    # Configure app logger
    app.logger.handlers.clear()
    app.logger.addHandler(console_handler)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(error_handler)
    app.logger.setLevel(logging.INFO)
    
    # Configure other loggers
    loggers = [
        'ai_integration',
        'database',
        'auth',
        'file_operations',
        'maps',
        'exports'
    ]
    
    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.addHandler(file_handler)
        logger.addHandler(error_handler)
        if app.debug:
            logger.addHandler(console_handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    
    return app.logger

def log_request_response(f):
    """Decorator to log API requests and responses"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # Generate request ID
        import uuid
        g.request_id = str(uuid.uuid4())[:8]
        
        logger = logging.getLogger('api')
        
        # Log request
        logger.info(f"API Request: {request.method} {request.path}", extra={
            'request_id': g.request_id,
            'endpoint': request.endpoint,
            'query_args': dict(request.args),
            'json': request.get_json() if request.is_json else None
        })
        
        try:
            # Execute the function
            start_time = datetime.utcnow()
            result = f(*args, **kwargs)
            end_time = datetime.utcnow()
            
            # Log successful response
            duration = (end_time - start_time).total_seconds()
            logger.info(f"API Response: {request.method} {request.path} - Success", extra={
                'request_id': g.request_id,
                'duration_seconds': duration,
                'status_code': getattr(result, 'status_code', 200)
            })
            
            return result
            
        except Exception as e:
            # Log error
            logger.error(f"API Error: {request.method} {request.path} - {str(e)}", extra={
                'request_id': g.request_id,
                'error_type': type(e).__name__,
                'error_message': str(e)
            }, exc_info=True)
            raise
    
    return decorated_function

def log_database_operation(operation, table=None, record_id=None, data=None):
    """Log database operations"""
    logger = logging.getLogger('database')
    logger.info(f"Database operation: {operation}", extra={
        'operation': operation,
        'table': table,
        'record_id': record_id,
        'data_keys': list(data.keys()) if data else None,
        'request_id': _get_request_id()
    })

def log_ai_operation(operation, model=None, tokens=None, duration=None, success=True, error=None):
    """Log AI/ML operations"""
    logger = logging.getLogger('ai_integration')
    
    log_data = {
        'operation': operation,
        'model': model,
        'tokens_used': tokens,
        'duration_seconds': duration,
        'success': success,
        'request_id': _get_request_id()
    }
    
    if error:
        log_data['error'] = str(error)
        logger.error(f"AI operation failed: {operation}", extra=log_data)
    else:
        logger.info(f"AI operation: {operation}", extra=log_data)

def log_file_operation(operation, filename, size=None, success=True, error=None):
    """Log file operations"""
    logger = logging.getLogger('file_operations')
    
    log_data = {
        'operation': operation,
        'file_name': filename,  # Changed from 'filename' to avoid conflict
        'file_size': size,
        'success': success,
        'request_id': _get_request_id()
    }
    
    if error:
        log_data['error'] = str(error)
        logger.error(f"File operation failed: {operation}", extra=log_data)
    else:
        logger.info(f"File operation: {operation}", extra=log_data)

def log_user_action(action, user_id=None, details=None):
    """Log user actions for audit trail"""
    logger = logging.getLogger('audit')
    logger.info(f"User action: {action}", extra={
        'action': action,
        'user_id': user_id,
        'details': details,
        'request_id': _get_request_id(),
        'ip_address': _get_request_info().get('remote_addr') if _get_request_info() else None
    })