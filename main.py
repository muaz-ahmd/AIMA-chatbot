import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import ChatbotConfig
from core.chatbot import HybridChatbot

class ChatbotCLI:
    """Command-line interface for chatbot"""
    
    def __init__(self, user_override: str = None):
        self.config = ChatbotConfig()
        self.chatbot = HybridChatbot(self.config, user_override=user_override)
        self.running = False
    
    def print_banner(self):
        """Print welcome banner"""
        banner = """
    .----------------.  .----------------.  .----------------.  .----------------. 
   | .--------------. || .--------------. || .--------------. || .--------------. |
   | |      __      | || |     _____    | || | ____    ____ | || |      __      | |
   | |     /  \\     | || |    |_   _|   | || ||_   \\  /   _|| || |     /  \\     | |
   | |    / /\\ \\    | || |      | |     | || |  |   \\/   |  | || |    / /\\ \\    | |
   | |   / ____ \\   | || |      | |     | || |  | |\\  /| |  | || |   / ____ \\   | |
   | | _/ /    \\ \\_ | || |     _| |_    | || | _| |_\\/_| |_ | || | _/ /    \\ \\_ | |
   | ||____|  |____|| || |    |_____|   | || ||_____||_____|| || ||____|  |____|| |
   | |              | || |              | || |              | || |              | |
   | '--------------' || '--------------' || '--------------' || '--------------' |
   '----------------'  '----------------'  '----------------'  '----------------' 
                            
                       AIMA ChatBot v1.0
             Advanced Intelligent Multi-purpose Agent
    """
        print(banner)
    
    def setup(self):
        """Initial setup"""
        print("\n" + "="*60)
        print("SETUP")
        print("="*60)
        
        # API Key: prefer environment variable if present
        env_api_key = os.environ.get("GEMINI_API_KEY")
        if env_api_key:
            print("\nUsing GEMINI_API_KEY from environment.")
            api_key = env_api_key
        else:
            # API Key prompt
            print("\nGemini API Configuration")
            print("Enter your Gemini API key (or press Enter to use local only):")
            api_key = input("API Key: ").strip()

            if not api_key:
                print("\nNo API key provided. Running in LOCAL-ONLY mode.")
                print("Only pattern-matched responses will be available.")
        
        # Initialize chatbot
        print("\nInitializing chatbot...")
        if self.chatbot.initialize(api_key if api_key else None):
            print("Chatbot initialized successfully.")
        else:
            print("Initialization failed. Starting with limited functionality.")
        
        print("\n" + "="*60)
        print("READY TO CHAT")
        print("="*60)
        print("\nTips:")
        print(" - Type 'help' for available commands")
        print(" - Type 'stats' to see usage statistics")
        print(" - Type 'quit' or 'exit' to end the session")
        print(" - Press Ctrl+C to force quit")
        print("\n" + "-"*60 + "\n")
    
    def run(self):
        """Main CLI loop"""
        self.running = True
        
        try:
            while self.running:
                # Get user input
                user_input = input(f"\n{self.config.prompt_symbol}").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if self.handle_command(user_input):
                    continue
                
                # Show typing indicator
                if self.config.show_typing_indicator:
                    print(f"\n{self.config.bot_symbol}", end="", flush=True)
                    import time
                    time.sleep(self.config.typing_delay)
                    print("\r" + " " * 50 + "\r", end="", flush=True)
                
                # Get response
                response = self.chatbot.process_input(user_input)
                
                # Display response
                print(f"{self.config.bot_symbol}{response}")
        
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            self.shutdown()
        except Exception as e:
            print(f"\n\nFatal error: {e}")
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
            print("Conversation history cleared")
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
        help_text = """
HELP & COMMANDS

Available Commands:
    help     - Show this help message
    stats    - Display usage statistics
    config   - Show current configuration
    clear    - Clear conversation history
    quit     - Exit the chatbot
    exit     - Exit the chatbot
    train    - Manually teach the bot a new response
    autolearn [on/off] - Toggle auto-learning from AI

Usage:
    Type your message and press Enter. The chatbot will:
    1. Check local patterns first (fast responses)
    2. Fall back to Gemini AI for complex queries
    3. Show response source: [LOCAL] or [GEMINI]

Features:
    - Conversation history & context
    - Response caching for speed
    - Fuzzy pattern matching
    - Rate limiting protection
    - Comprehensive logging
                """
        print(help_text)
    
    def show_stats(self):
        """Show statistics"""
        stats = self.chatbot.get_statistics()
        
        print("\n" + "="*60)
        print("CHATBOT STATISTICS")
        print("="*60)
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
        print("="*60)
    
    def show_config(self):
        """Show configuration"""
        print("\n" + "="*60)
        print("CONFIGURATION")
        print("="*60)
        print(f"\nKey Settings:")
        print(f"   Gemini Model:           {self.config.gemini_model}")
        print(f"   Local Priority:         {self.config.enable_local_priority}")
        print(f"   Fuzzy Matching:         {self.config.use_fuzzy_matching}")
        print(f"   Response Cache:         {self.config.enable_response_cache}")
        print(f"   Context Enabled:        {self.config.enable_context}")
        print(f"   Max History:            {self.config.max_history_length}")
        print(f"   Max History:            {self.config.max_history_length}")
        print(f"   Rate Limit:             {self.config.max_requests_per_minute}/min")
        print(f"   Auto Learning:          {self.config.enable_auto_learning}")
        print("="*60)
    
    def train_mode(self):
        """Interactive training mode"""
        print("\n" + "="*60)
        print("TRAINING MODE")
        print("="*60)
        print("Teach the bot a new pattern. Type 'cancel' to exit.")
        
        while True:
            pattern = input("\n[1] What should I listen for? (Pattern): ").strip()
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
                print(f"✓ Learned: '{pattern}' -> '{response}'")
                break
            else:
                print("x Failed to save pattern.")
                break
        print("="*60)

    def handle_autolearn(self, cmd: str) -> bool:
        """Toggle auto-learning"""
        parts = cmd.split()
        if len(parts) > 1:
            state = parts[1].lower()
            if state in ['on', 'true', '1']:
                self.config.enable_auto_learning = True
                print("Auto-learning ENABLED")
            elif state in ['off', 'false', '0']:
                self.config.enable_auto_learning = False
                print("Auto-learning DISABLED")
            else:
                print("Usage: autolearn [on/off]")
        else:
            print(f"Auto-learning is currently: {'ENABLED' if self.config.enable_auto_learning else 'DISABLED'}")
        return True

    def shutdown(self):
        """Graceful shutdown"""
        print("\n" + "="*60)
        print("SHUTTING DOWN")
        print("="*60)
        
        self.chatbot.shutdown()
        
        print("\nThanks for chatting. Goodbye!")
        print("="*60 + "\n")
        
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