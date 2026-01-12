"""Configuration management for BuffersBot."""
import json
from customtkinter import filedialog


class ConfigManager:
    """Manages saving and loading of application configuration."""
    
    @staticmethod
    def save_config(config_data, on_success_callback=None):
        """Save configuration to a JSON file.
        
        Args:
            config_data: Dictionary containing configuration data
            on_success_callback: Optional callback function to call on success
        """
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if filename:
            with open(filename, "w") as config_file:
                json.dump(config_data, config_file, indent=4)
            if on_success_callback:
                on_success_callback(f"Configuration saved to {filename}!")
            return True
        return False
    
    @staticmethod
    def load_config(on_success_callback=None, on_error_callback=None):
        """Load configuration from a JSON file.
        
        Args:
            on_success_callback: Optional callback function to call on success
            on_error_callback: Optional callback function to call on error
            
        Returns:
            Dictionary containing configuration data or None if cancelled
        """
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")]
        )
        if filename:
            try:
                with open(filename, "r") as config_file:
                    config = json.load(config_file)
                if on_success_callback:
                    on_success_callback(f"Configuration loaded from {filename}")
                return config
            except Exception as e:
                if on_error_callback:
                    on_error_callback(f"Error loading config: {str(e)}")
                return None
        else:
            if on_error_callback:
                on_error_callback("No file selected.")
            return None
