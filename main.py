import sys
import os
from pathlib import Path
import threading

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import ChatbotConfig
from core.chatbot import HybridChatbot
from utils.ui_enhancements import UIManager, Colors

class ChatbotCLI:
    """Command-line interface for chatbot"""
    
    def __init__(self, user_override: str = None):
        self.config = ChatbotConfig()
        self.chatbot = HybridChatbot(self.config, user_override=user_override)
        self.ui = UIManager(enable_colors=self.config.enable_colors)
        self.running = False
    
    def print_banner(self):
        """Print welcome banner with fire effect (yellow top to red bottom)"""
        banner_lines = [
            '                  __        __     ___      ___       __      ',
            '                 /""\      |" \\   |"  \\    /"  |     /""\     ',
            '                /    \\     ||  |   \\   \\  //   |    /    \\    ',
            '               /\' /\\  \\    |:  |   /\\   \\/.    |   /\' /\\  \\   ',
            '              //  __\'  \\   |.  |  |: \\.        |  //  __\'  \\  ',
            '             /   /  \\\\  \\  /\\  |\\ |.  \\    /:  | /   /  \\\\  \\ ',
            '            (___/    \\___)(__\\_|_)|___ \\__/|___|(___/    \\___))',
            '                                                  ',
            '                          AIMA ChatBot v1.0',
            '                Advanced Intelligent Multi-purpose Agent'
        ]
        
        # Color mapping: top lines yellow, middle orange/red, bottom red for fire effect
        colors = [
            Colors.LIGHT_YELLOW,  # Line 1 - bright yellow
            Colors.LIGHT_YELLOW,  # Line 2 - bright yellow
            Colors.YELLOW,        # Line 3 - yellow
            Colors.ORANGE,        # Line 4 - orange
            Colors.ORANGE,        # Line 5 - orange
            Colors.LIGHT_RED,     # Line 6 - light red
            Colors.RED,           # Line 7 - red
            Colors.LIGHT_GRAY,    # Line 8 - spacing
            Colors.LIGHT_YELLOW,  # Line 9 - title in bright yellow
            Colors.YELLOW         # Line 10 - subtitle in yellow
        ]
        
        print()  # Top spacing
        for line, color in zip(banner_lines, colors):
            print(f"{color}{line}{Colors.RESET}")
        print()  # Bottom spacing
    
    def setup(self):
        """Initial setup"""
        self.ui.print_banner("SETUP")
        
        # API Key: prefer environment variable if present
        env_api_key = os.environ.get("GEMINI_API_KEY")
        if env_api_key:
            self.ui.print_system_message("Using GEMINI_API_KEY from environment.", "INFO")
            api_key = env_api_key
        else:
            # API Key prompt
            print("\n" + "Gemini API Configuration".center(60))
            print("Enter your Gemini API key (or press Enter to use local only):")
            api_key = input("API Key: ").strip()

            if not api_key:
                self.ui.print_system_message("No API key provided. Running in LOCAL-ONLY mode.", "WARNING")
                print("Only pattern-matched responses will be available.")
        
        # Initialize chatbot
        print("\nInitializing chatbot...")
        if self.chatbot.initialize(api_key if api_key else None):
            self.ui.print_system_message("Chatbot initialized successfully.", "SUCCESS")
        else:
            self.ui.print_system_message("Initialization failed. Starting with limited functionality.", "WARNING")
        
        self.ui.print_banner("READY TO CHAT")
        print(f"\n{Colors.LIGHT_YELLOW}Tips:")
        print(f"→ Type 'help' for available commands")
        print(f"→ Type 'stats' to see usage statistics")
        print(f"→ Type 'quit' or 'exit' to end the session")
        print(f"→ Press Ctrl+C to force quit{Colors.RESET}")
        print("\n" + "-"*60 + "\n")
    
    def run(self):
        """Main CLI loop"""
        self.running = True
        
        try:
            while self.running:
                # Get user input
                print()  # Add spacing
                user_input = input(f"{Colors.LIGHT_BLUE}You:{Colors.RESET} ").strip()
                print()  # New line after input
                
                if not user_input:
                    continue
                
                # Handle commands
                if self.handle_command(user_input):
                    continue
                
                # Get response (shows typing indicator if enabled, then processes)
                response = self.chatbot.process_input(user_input)
                
                # Extract source if available (format: [SOURCE]response)
                source = None
                if response.startswith('[') and ']' in response:
                    end_bracket = response.index(']')
                    source = response[1:end_bracket]
                    response = response[end_bracket+1:].strip()
                
                # Display response: source in grey, Bot in green, rest normal
                if source:
                    print(f"{Colors.LIGHT_GRAY}[{source}]{Colors.RESET} {Colors.GREEN}Bot:{Colors.RESET} {response}")
                else:
                    print(f"{Colors.GREEN}Bot:{Colors.RESET} {response}")
        
        except KeyboardInterrupt:
            print("\n")
            self.ui.print_system_message("Interrupted by user", "INFO")
            self.shutdown()
        except Exception as e:
            print("\n")
            self.ui.print_system_message(f"Fatal error: {e}", "ERROR")
            self.shutdown()
    
    def handle_command(self, command: str) -> bool:
        """Handle special commands"""
        cmd = command.lower()
        
        if cmd in ['quit', 'exit', 'bye']:
            self.shutdown()
            return True
        
        elif cmd == 'help':
            self.show_help()
            return True
        
        elif cmd == 'stats':
            self.show_stats()
            return True
        
        elif cmd == 'clear':
            self.chatbot.clear_history()
            self.ui.print_system_message("Conversation history cleared", "SUCCESS")
            return True
        
        elif cmd == 'config':
            self.show_config()
            return True

        elif cmd.startswith('autolearn'):
            return self.handle_autolearn(cmd)

        elif cmd == 'train':
            self.train_mode()
            return True
        
        return False
    
    def show_help(self):
        """Show help information"""
        self.ui.print_banner("HELP & COMMANDS")
        print(f"{Colors.LIGHT_YELLOW}")
        help_text = """
Available Commands:
→ help     - Show this help message
→ stats    - Display usage statistics
→ config   - Show current configuration
→ clear    - Clear conversation history
→ quit     - Exit the chatbot
→ exit     - Exit the chatbot
→ train    - Manually teach the bot a new response
→ autolearn [on/off] - Toggle auto-learning from AI

Usage:
Type your message and press Enter. The chatbot will:
1. Check local patterns first (fast responses)
2. Fall back to Gemini AI for complex queries
3. Show response source: [LOCAL] or [GEMINI]

Features:
→ Conversation history & context
→ Response caching for speed
→ Fuzzy pattern matching
→ Rate limiting protection
→ Comprehensive logging
        """
        print(help_text)
        print(f"{Colors.RESET}")
    
    def show_stats(self):
        """Show statistics"""
        stats = self.chatbot.get_statistics()
        
        self.ui.print_banner("CHATBOT STATISTICS")
        print(f"\nSession Stats:")
        print(f"   Total Queries:     {stats['total_queries']}")
        print(f"   Local Responses:   {stats['local_responses']}")
        print(f"   AI Responses:      {stats['ai_responses']}")
        print(f"   Cache Hits:        {stats['cache_hits']}")
        print(f"   Errors:            {stats['errors']}")
        print(f"\nPerformance:")
        print(f"   Uptime:            {stats['uptime_seconds']:.1f}s")
        print(f"   Cache Size:        {stats['cache_size']} entries")
        print(f"   History Length:    {stats['history_length']} exchanges")
    
    def show_config(self):
        """Show configuration"""
        self.ui.print_banner("CONFIGURATION")
        print(f"\nKey Settings:")
        print(f"   Gemini Model:           {self.config.gemini_model}")
        print(f"   Local Priority:         {self.config.enable_local_priority}")
        print(f"   Fuzzy Matching:         {self.config.use_fuzzy_matching}")
        print(f"   Response Cache:         {self.config.enable_response_cache}")
        print(f"   Context Enabled:        {self.config.enable_context}")
        print(f"   Max History:            {self.config.max_history_length}")
        print(f"   Rate Limit:             {self.config.max_requests_per_minute}/min")
        print(f"   Auto Learning:          {self.config.enable_auto_learning}")
    
    def train_mode(self):
        """Interactive training mode"""
        self.ui.print_banner("TRAINING MODE")
        print("Teach the bot a new pattern. Type 'cancel' to exit.")
        
        while True:
            print()
            pattern = input("[1] What should I listen for? (Pattern): ").strip()
            if pattern.lower() == 'cancel':
                break
            if not pattern:
                continue
                
            response = input("[2] What should I say? (Response): ").strip()
            if response.lower() == 'cancel':
                break
            if not response:
                continue
            
            if self.chatbot.learn_pattern(pattern, response):
                self.ui.print_system_message(f"Learned: '{pattern}' -> '{response}'", "SUCCESS")
                break
            else:
                self.ui.print_system_message("Failed to save pattern.", "ERROR")
                break

    def handle_autolearn(self, cmd: str) -> bool:
        """Toggle auto-learning"""
        parts = cmd.split()
        if len(parts) > 1:
            state = parts[1].lower()
            if state in ['on', 'true', '1']:
                self.config.enable_auto_learning = True
                self.ui.print_system_message("Auto-learning ENABLED", "SUCCESS")
            elif state in ['off', 'false', '0']:
                self.config.enable_auto_learning = False
                self.ui.print_system_message("Auto-learning DISABLED", "WARNING")
            else:
                self.ui.print_system_message("Usage: autolearn [on/off]", "INFO")
        else:
            status = 'ENABLED' if self.config.enable_auto_learning else 'DISABLED'
            self.ui.print_system_message(f"Auto-learning is currently: {status}", "INFO")
        return True

    def shutdown(self):
        """Graceful shutdown"""
        self.ui.print_banner("SHUTTING DOWN")
        
        self.chatbot.shutdown()
        
        self.ui.print_system_message("Thanks for chatting. Goodbye!", "SUCCESS")
        
        self.running = False
        sys.exit(0)

def main():
    """Entry point"""
    import argparse
    parser = argparse.ArgumentParser(description="AIMA ChatBot")
    parser.add_argument("--user", type=str, help="Override user identity", default=None)
    args = parser.parse_args()

    cli = ChatbotCLI(user_override=args.user)
    cli.print_banner()
    cli.setup()
    cli.run()

if __name__ == "__main__":
    main()