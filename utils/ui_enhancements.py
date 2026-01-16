"""
Enhanced UI utilities for terminal-based chatbot
Provides:
- Typing indicator animation
- Markdown rendering
- Color coding
- Visual separation
"""

import sys
import time
import re
from typing import Optional
from enum import Enum


class Colors(Enum):
    """ANSI color codes"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    
    # Foreground colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Light colors
    LIGHT_GRAY = '\033[90m'
    LIGHT_RED = '\033[91m'
    LIGHT_GREEN = '\033[92m'
    LIGHT_YELLOW = '\033[93m'
    LIGHT_BLUE = '\033[94m'
    LIGHT_MAGENTA = '\033[95m'
    LIGHT_CYAN = '\033[96m'
    LIGHT_WHITE = '\033[97m'
    
    # Special colors
    ORANGE = '\033[38;5;208m'
    
    def __str__(self):
        return self.value


class TypingIndicator:
    """Animated typing indicator"""
    
    def __init__(self, message: str = "Thinking", delay: float = 0.1):
        """
        Initialize typing indicator
        
        Args:
            message: Message to display before animation
            delay: Delay between animation frames in seconds
        """
        self.message = message
        self.delay = delay
        self.frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.running = False
    
    def start(self):
        """Start typing indicator animation"""
        self.running = True
        frame_index = 0
        
        while self.running:
            frame = self.frames[frame_index % len(self.frames)]
            sys.stdout.write(f'\r{Colors.CYAN}{frame} {self.message}...{Colors.RESET}')
            sys.stdout.flush()
            time.sleep(self.delay)
            frame_index += 1
    
    def stop(self):
        """Stop typing indicator and clear the line"""
        self.running = False
        sys.stdout.write('\r' + ' ' * 50 + '\r')
        sys.stdout.flush()


class MarkdownRenderer:
    """Renders markdown formatting in terminal"""
    
    @staticmethod
    def render(text: str) -> str:
        """
        Render markdown in terminal
        
        Supports:
        - **bold** -> bold text
        - *italic* -> italic text
        - _italic_ -> italic text
        - `code` -> colored code
        - # Header -> colored header
        - ## Subheader -> colored subheader
        - - List item -> formatted list
        
        Args:
            text: Markdown text to render
            
        Returns:
            ANSI-formatted text
        """
        # Process headers
        text = MarkdownRenderer._render_headers(text)
        
        # Process code blocks (backticks)
        text = MarkdownRenderer._render_code(text)
        
        # Process bold
        text = MarkdownRenderer._render_bold(text)
        
        # Process italic
        text = MarkdownRenderer._render_italic(text)
        
        # Process lists
        text = MarkdownRenderer._render_lists(text)
        
        # Process line breaks
        text = MarkdownRenderer._render_line_breaks(text)
        
        return text
    
    @staticmethod
    def _render_headers(text: str) -> str:
        """Render markdown headers"""
        # H1: # Header
        text = re.sub(
            r'^# (.+)$',
            lambda m: f'{Colors.BOLD}{Colors.LIGHT_CYAN}# {m.group(1)}{Colors.RESET}',
            text,
            flags=re.MULTILINE
        )
        
        # H2: ## Header
        text = re.sub(
            r'^## (.+)$',
            lambda m: f'{Colors.BOLD}{Colors.CYAN}## {m.group(1)}{Colors.RESET}',
            text,
            flags=re.MULTILINE
        )
        
        # H3: ### Header
        text = re.sub(
            r'^### (.+)$',
            lambda m: f'{Colors.BOLD}{Colors.BLUE}### {m.group(1)}{Colors.RESET}',
            text,
            flags=re.MULTILINE
        )
        
        return text
    
    @staticmethod
    def _render_code(text: str) -> str:
        """Render inline code"""
        # Match backticks but not in already processed areas
        text = re.sub(
            r'`([^`]+)`',
            lambda m: f'{Colors.LIGHT_GRAY}{m.group(1)}{Colors.RESET}',
            text
        )
        return text
    
    @staticmethod
    def _render_bold(text: str) -> str:
        """Render bold text"""
        # Match **text** but avoid nested formatting issues
        text = re.sub(
            r'\*\*([^\*]+)\*\*',
            lambda m: f'{Colors.BOLD}{m.group(1)}{Colors.RESET}',
            text
        )
        return text
    
    @staticmethod
    def _render_italic(text: str) -> str:
        """Render italic text"""
        # Match *text* or _text_ (but not in **text**)
        # Avoid matching ** patterns
        text = re.sub(
            r'(?<!\*)\*([^\*]+)\*(?!\*)',
            lambda m: f'{Colors.ITALIC}{m.group(1)}{Colors.RESET}',
            text
        )
        text = re.sub(
            r'_([^_]+)_',
            lambda m: f'{Colors.ITALIC}{m.group(1)}{Colors.RESET}',
            text
        )
        return text
    
    @staticmethod
    def _render_lists(text: str) -> str:
        """Render markdown lists"""
        # Unordered lists: - Item or * Item
        text = re.sub(
            r'^[-*] (.+)$',
            lambda m: f'{Colors.LIGHT_GREEN}→ {m.group(1)}{Colors.RESET}',
            text,
            flags=re.MULTILINE
        )
        
        # Ordered lists: 1. Item
        text = re.sub(
            r'^(\d+)\. (.+)$',
            lambda m: f'{Colors.LIGHT_GREEN}{m.group(1)}. {m.group(2)}{Colors.RESET}',
            text,
            flags=re.MULTILINE
        )
        
        return text
    
    @staticmethod
    def _render_line_breaks(text: str) -> str:
        """Add spacing for line breaks"""
        return text


class MessageFormatter:
    """Formats messages with color coding and visual separation"""
    
    @staticmethod
    def format_user_message(message: str, symbol: str = "You: ") -> str:
        """
        Format user message
        
        Args:
            message: User's input message
            symbol: Prefix symbol
            
        Returns:
            Formatted message
        """
        prefix = f'{Colors.WHITE}{symbol}{Colors.RESET}'
        separator = f'{Colors.LIGHT_GRAY}{"─" * 58}{Colors.RESET}'
        return f'{separator}\n{prefix}{message}'
    
    @staticmethod
    def format_ai_message(message: str, symbol: str = "Bot: ", source: str = None) -> str:
        """
        Format AI response message
        
        Args:
            message: AI's response message
            symbol: Prefix symbol
            source: Source of response (e.g., "LOCAL", "GEMINI", "CACHED")
            
        Returns:
            Formatted message
        """
        # Render markdown
        rendered = MarkdownRenderer.render(message)
        
        # Format prefix with color
        prefix = f'{Colors.GREEN}{symbol}{Colors.RESET}'
        
        # Add source indicator if provided
        source_str = ""
        if source:
            source_colors = {
                "LOCAL": Colors.LIGHT_CYAN,
                "GEMINI": Colors.LIGHT_BLUE,
                "CACHED": Colors.LIGHT_YELLOW,
            }
            color = source_colors.get(source, Colors.LIGHT_GRAY)
            source_str = f' {color}[{source}]{Colors.RESET}'
        
        separator = f'{Colors.LIGHT_GRAY}{"─" * 58}{Colors.RESET}'
        return f'{separator}\n{prefix}{source_str}\n{rendered}'
    
    @staticmethod
    def format_log_message(message: str, level: str = "INFO") -> str:
        """
        Format log message with color coding
        
        Args:
            message: Log message
            level: Log level (DEBUG, INFO, WARNING, ERROR)
            
        Returns:
            Formatted message
        """
        level_colors = {
            "DEBUG": Colors.LIGHT_GRAY,
            "INFO": Colors.YELLOW,
            "WARNING": Colors.LIGHT_YELLOW,
            "ERROR": Colors.LIGHT_RED,
        }
        
        color = level_colors.get(level, Colors.WHITE)
        return f'{color}[{level}]{Colors.RESET} {message}'
    
    @staticmethod
    def format_system_message(message: str, message_type: str = "INFO") -> str:
        """
        Format system message
        
        Args:
            message: System message
            message_type: Type (INFO, WARNING, ERROR, SUCCESS)
            
        Returns:
            Formatted message
        """
        type_info = {
            "INFO": (Colors.LIGHT_BLUE, "ℹ"),
            "WARNING": (Colors.LIGHT_YELLOW, "⚠"),
            "ERROR": (Colors.LIGHT_RED, "✗"),
            "SUCCESS": (Colors.LIGHT_GREEN, "✓"),
        }
        
        color, symbol = type_info.get(message_type, (Colors.WHITE, "→"))
        separator = f'{Colors.LIGHT_GRAY}{"─" * 58}{Colors.RESET}'
        
        return f'{separator}\n{color}{symbol} {message}{Colors.RESET}'
    
    @staticmethod
    def format_banner(title: str) -> str:
        """
        Format a banner/header
        
        Args:
            title: Banner title
            
        Returns:
            Formatted banner
        """
        line = f'{Colors.LIGHT_CYAN}{"=" * 60}{Colors.RESET}'
        title_str = f'{Colors.BOLD}{Colors.LIGHT_CYAN}{title.center(60)}{Colors.RESET}'
        return f'{line}\n{title_str}\n{line}'


class UIManager:
    """High-level UI management"""
    
    def __init__(self, enable_colors: bool = True):
        """
        Initialize UI manager
        
        Args:
            enable_colors: Whether to enable color output
        """
        self.enable_colors = enable_colors
        self.typing_indicator = None
    
    def start_typing(self, message: str = "Thinking", delay: float = 0.1):
        """Start typing indicator in a separate thread"""
        import threading
        self.typing_indicator = TypingIndicator(message, delay)
        thread = threading.Thread(target=self.typing_indicator.start, daemon=True)
        thread.start()
    
    def stop_typing(self):
        """Stop typing indicator"""
        if self.typing_indicator:
            self.typing_indicator.stop()
            self.typing_indicator = None
    
    def print_user_message(self, message: str):
        """Print formatted user message"""
        formatted = MessageFormatter.format_user_message(message)
        print(formatted)
    
    def print_ai_message(self, message: str, source: str = None):
        """Print formatted AI message"""
        formatted = MessageFormatter.format_ai_message(message, source=source)
        print(formatted)
    
    def print_log(self, message: str, level: str = "INFO"):
        """Print formatted log message"""
        if self.enable_colors:
            formatted = MessageFormatter.format_log_message(message, level)
            print(formatted)
        else:
            print(f"[{level}] {message}")
    
    def print_system_message(self, message: str, message_type: str = "INFO"):
        """Print formatted system message"""
        if self.enable_colors:
            formatted = MessageFormatter.format_system_message(message, message_type)
            print(formatted)
        else:
            print(f"[{message_type}] {message}")
    
    def print_banner(self, title: str):
        """Print formatted banner"""
        if self.enable_colors:
            formatted = MessageFormatter.format_banner(title)
            print(formatted)
        else:
            print("=" * 60)
            print(title.center(60))
            print("=" * 60)
