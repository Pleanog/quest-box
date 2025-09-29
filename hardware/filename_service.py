import os

class FileNameService:
    """Provides utility methods for formatting game and path names into file paths."""
    
    def __init__(self, base_dir: str):
        self.BASE_DIR = base_dir
        self.GAMES_FOLDER = 'games'

    def get_game_folder_path(self, game_name: str) -> str:
        """Returns the full path to the game's main folder."""
        return os.path.join(self.BASE_DIR, self.GAMES_FOLDER, game_name)

    def get_audio_folder_path(self, game_name: str) -> str:
        """Returns the full path to the game's audio folder."""
        return os.path.join(self.get_game_folder_path(game_name), 'audio')

    def get_game_json_path(self, game_name: str) -> str:
        """Returns the full path to the main game JSON configuration file."""
        return os.path.join(self.get_game_folder_path(game_name), f"{game_name}.json")

    def get_audio_filename(self, type_prefix: str, path_name: str) -> str:
        """
        Creates a consistent audio filename (e.g., 'hint_the_sheriffs_safe.mp3').
        
        Args:
            type_prefix (str): 'starting_description', 'hint', 'description', or 'death_text'.
            path_name (str): The value from the JSON's 'path_name' key.
            
        Returns:
            str: The sanitized filename.
        """
        # 1. Sanitize the path_name (assuming path_name is already file-safe)
        sanitized_path_name = path_name.lower().replace(' ', '_').replace('-', '_')
        
        # 2. Construct the filename
        # Special case for the starting description which uses the game name as the path identifier
        if type_prefix == 'starting_description':
             return f"{type_prefix}_{sanitized_path_name}.mp3"
        
        return f"{type_prefix}_{sanitized_path_name}.mp3"