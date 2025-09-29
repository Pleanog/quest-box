import google.generativeai as genai
import os
import json
import codecs
from dotenv import load_dotenv
from colorama import Fore, Style
from hardware.filename_service import FileNameService 

# colorama.init(autoreset=True)

# Define the base directory for the entire project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# GAMES_DIR = os.path.join(BASE_DIR, 'games')
# AVAILABLE_GAMES_FILE = os.path.join(GAMES_DIR, 'available_games.txt')
file_service = FileNameService(BASE_DIR)

def _sanitize_game_name(title: str) -> str:
    """Converts a title into a file-safe, lowercase, hyphenated name."""
    # Convert to lowercase and replace spaces/non-alphanumeric chars with hyphens
    return title.lower().strip().replace(' ', '-').replace("'", "").replace(":", "").replace("!", "")

def _register_new_game(game_name: str) -> None:
    games_dir = file_service.get_game_folder_path("") # Gets the 'games' directory
    available_games_file = os.path.join(games_dir, 'available_games.txt')
    """Adds the new game name to the available_games.txt file."""
    try:
        if not os.path.exists(games_dir):
            os.makedirs(games_dir)
            
        # Append the new game name to the file with a newline
        with open(available_games_file, 'a') as f:
            f.write(f"{game_name}\n")
        print(f"{Fore.GREEN}Game registered in: {available_games_file}{Style.RESET_ALL}")
    except IOError as e:
        print(f"{Fore.RED}Error registering game: {e}{Style.RESET_ALL}")


"""
Generates a new room.json configuration by calling the Gemini API.

Returns:
    str: The name of the generated game or None if the generation failed.
"""
def generate_room_configuration() -> str | None:
    # Load environment variables
    load_dotenv()
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    
    if not gemini_api_key:
        print(f"{Fore.RED}Error: GEMINI_API_KEY not found in .env file.{Style.RESET_ALL}")
        return None
        
    genai.configure(api_key=gemini_api_key)

    # --- Existing file paths for templates (Using BASE_DIR for better flexibility) ---
    template_file_path = os.path.join(BASE_DIR, 'geminiAPI', 'rooms_template.json')
    example_file_path = os.path.join(BASE_DIR, 'geminiAPI', 'rooms_example.json')

    # 1. Read the JSON files
    try:
        with open(template_file_path, 'r') as file:
            json_template_data = json.load(file)

        with open(example_file_path, 'r') as file:
            json_example_data = json.load(file)
    except FileNotFoundError as e:
        print(f"{Fore.RED}Error reading template/example files: {e}{Style.RESET_ALL}")
        return None
    except json.JSONDecodeError as e:
        print(f"{Fore.RED}Error decoding JSON in template/example files: {e}{Style.RESET_ALL}")
        return None

    # 2. Convert the Python dictionary to a JSON string (Prompt Generation)
    json_template_string = json.dumps(json_template_data, indent=2)
    json_example_string = json.dumps(json_example_data, indent=2)

    prompt = f"""
    You are a Master Riddle Designer for a physical puzzle box. Your primary goal is to create puzzles where the "hint" provides a clear, logical, and solvable path to the "solution_sequence". The player must be able to deduce the correct actions by thinking critically about the hint and the story's context.

    Your task is to populate the empty fields in the following JSON structure.

    Here is the JSON structure you need to populate:
    {json_template_string}

    Here is an example of a perfectly designed, solvable path for your reference:
    {json_example_string}

    Here are the constraints and the process you must follow:

    **Overall Story:**
    - "title": A creative title for the story.
    - "starting_description": A compelling starting point for the adventure that sets the scene.
    - "themes": The story's theme must be one of the provided options.

    **Path Design (For each of the 3 paths):**
    1.  **First, decide on a logical `solution_sequence`** between 2 and 4 steps long, fitting the theme.
    2.  **Second, for each step in your `solution_sequence`, you must devise a clear logical reason why a clue would point to it.** This is your internal "Hint Logic".
    3.  **Third, write the `hint` based on your Hint Logic.** The hint must be a single string containing individual clues. Each clue must directly and logically point to the corresponding step in the `solution_sequence`. The first clue guides the first step, the second clue guides the second step, and so on.
        - **Clarity over Obscurity:** The hint should be clever and thematic, but NOT so cryptic that it's unsolvable. A player must be able to solve it with the information given.
        - **Structure:** Separate the individual clues within the hint string with " // ".

    **Detailed Field Constraints:**
    - "inputs": Choose from: "button", "rotary_encoder_number", "rotary_encoder_picture", "gyro", "distance_sensor".
    - "buttonValues": Choose from: "red", "blue", "green", "yellow".
    - "rotaryEncoderNumberValues": A number from "1" to "10".
    - "rotaryEncoderPictureValues": An item from the list: "dynamite", "knife", "candle", "rope", "key", "book", "dice", "potion", "stick".
    - "gyroValues": Must be "shaking".
    - "distanceSensorValues": Choose from: "hovered", "covered".
    - "paths": You must create 3 unique and solvable adventure paths.
        - "hint": A string of clues separated by " // ". Must be logically solvable.
        - "solution_sequence": A list of 2 to 4 input objects.
        - "death_text": A creative description of failure that relates to the path's description.

    **Detailed Actuator Constraints:**
    - "actuators": Choose from the following options: "light", "vibration".
    - "lightModes": Choose from the following options: "static", "blink", "pulse", "fade".
    - "vibrationModes": Choose from the following options: "vibrate", "rattle".
    - "effectsColors": Choose from the following options: "red", "green", "blue", "yellow", "white", "purple".
    - "audio_cue": A sound effect to play.
    - "effects": Two effects to display selected from the "actuators" list. One actuator must be "light" and the other "vibration".
        - "actuator": The type of actuator ("light" or "vibration").
        - "mode": The type of effect (choose from "lightModes" for light actuators or "vibrationModes" for vibration actuators).
        - "duration": Duration of the effect in seconds (integer between 1 and 10). This only applies to vibration effects.
        - "color": The color of the effect (choose from "effectsColors"). This only applies to light effects.

    Please generate the complete JSON object. When generating the hints for the solution sequence, provide a logical explanation that connections each hint to the correct solution in the solution sequence. Put this explanation into a new variable called "Hint Logic" at the end of the JSON.
    Remove the Hint Logic variable before returning the final JSON.
    Provide only the final JSON in your response, with no additional text or explanation and do not put it in markdown.
    **Final and Most Important Rule:** Your entire response must be **only** the raw JSON text, starting with the opening curly brace and ending with the final closing curly brace. Do not include the markdown specifier ` ```json `, any other text, explanations, or formatting. The response must be a valid JSON object and nothing else.

    """

    # 3. Configure and call the model
    model = genai.GenerativeModel('gemini-2.5-flash')
    try:
        response = model.generate_content(prompt)
    except Exception as e:
        print(f"{Fore.RED}Error calling Gemini API: {e}{Style.RESET_ALL}")
        return None

    # 4. Save and Post-process the file
    try:
        raw_content = response.text
        
        cleaned_content = raw_content.strip()
        if cleaned_content.startswith('"') and cleaned_content.endswith('"'):
            cleaned_content = cleaned_content[1:-1]
        
        cleaned_content = codecs.decode(cleaned_content, 'unicode_escape')
        
        data = json.loads(cleaned_content)
        
        game_title = data.get("title", "untitled-game")
        game_name = _sanitize_game_name(game_title)
        
        game_folder_path = file_service.get_game_folder_path(game_name) # <--- USE SERVICE
        output_file_path = file_service.get_game_json_path(game_name)    # <--- USE SERVICE
                
        if not os.path.exists(game_folder_path):
            print(f"{Fore.YELLOW}Creating game directory: {game_folder_path}{Style.RESET_ALL}")
            os.makedirs(game_folder_path)

        with open(output_file_path, 'w', encoding='utf-8') as file:
             json.dump(data, file, indent=4)
        
        print(f"{Fore.GREEN}✅ Configuration saved to: {output_file_path}{Style.RESET_ALL}")

        _register_new_game(game_name)
        
        # Return the game name for use in main.py
        return game_name

    except json.JSONDecodeError as e:
        print(f"{Fore.RED}Error: Failed to parse valid JSON from Gemini output. Details: {e}{Style.RESET_ALL}")
        return None
    except Exception as e:
        print(f"{Fore.RED}An unexpected error occurred during file processing: {e}{Style.RESET_ALL}")
        return None

if __name__ == "__main__":
    generated_game_name = generate_room_configuration()
    if generated_game_name:
        print(f"\nGame configuration successfully generated and named: {Fore.CYAN}{generated_game_name}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Failed to generate room configuration.{Style.RESET_ALL}")