class AutoAbsenError(Exception):
    """Base exception for AutoAbsen application"""
    pass

class ConfigurationError(AutoAbsenError):
    """Raised when configuration is missing or invalid"""
    pass

class LoginError(AutoAbsenError):
    """Raised when login fails for MagangHub"""
    pass

class ContentGenerationError(AutoAbsenError):
    """Raised when AI fails to generate content"""
    pass

class AutomationError(AutoAbsenError):
    """Raised when SeleniumBase automation fails"""
    pass
