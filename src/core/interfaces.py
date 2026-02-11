from abc import ABC, abstractmethod
from typing import Dict, Any
from .entities import Report

class IContentGenerator(ABC):
    """
    Interface for AI Content Generators.
    Follows ISP: Clients only need to know about 'generate_content'.
    """
    @abstractmethod
    def generate_content(self, context: str, user_input: str) -> Report:
        pass

class IAutomationDriver(ABC):
    """
    Interface for Browser Automation Drivers.
    Follows DIP: High-level services depend on this abstraction.
    """
    @abstractmethod
    def login(self, email: str, password: str) -> bool: pass

    @abstractmethod
    def navigate_to_report_page(self) -> bool: pass

    @abstractmethod
    def fill_report(self, report: Report) -> bool: pass
        
    @abstractmethod
    def submit_report(self) -> bool: pass
        
    @abstractmethod
    def close(self): pass

class IInteractionHandler(ABC):
    """
    Interface for handling user interaction (Bot, CLI, API).
    """
    @abstractmethod
    def start(self):
        """Start listening for inputs"""
        pass
    
    @abstractmethod
    def stop(self):
        """Stop listening"""
        pass
