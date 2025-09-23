import google.generativeai as genai
import os
import json
import codecs
from dotenv import load_dotenv

"""
Generates a new room.json configuration by calling the Gemini API.

Returns:
    bool: True if the file was created successfully, False otherwise.
"""
def generate_room_configuration():
    # Load environment variables
    load_dotenv()
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    genai.configure(api_key=gemini_api_key)

    template_file_path = '/home/philipp/quest-box/geminiAPI/rooms_template.json'
    output_file_path = '/home/philipp/quest-box/geminiAPI/room.json'
    example_file_path = '/home/philipp/quest-box/geminiAPI/rooms_example.json'

    # 1. Read the JSON files
    with open(template_file_path, 'r') as file:
        json_template_data = json.load(file)

    with open(example_file_path, 'r') as file:
        json_example_data = json.load(file)

    # 2. Convert the Python dictionary to a JSON string
    json_template_string = json.dumps(json_template_data, indent=2)
    json_example_string = json.dumps(json_example_data, indent=2)

    # 3. Create a prompt that includes the JSON string
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
    - "buttonValues": Choose from: "red", "blue", "green", "yellow", "black".
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

    # Configure and call the model
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)

    # Print the generated JSON
    # print(response.text)

    try:
        with open(output_file_path, 'w') as json_file:
            # Use json.dump() to write the new data to the file
            json.dump(response.text, json_file, indent=4)
        print(f"Successfully replaced the content of '{output_file_path}' with the new data.")
    except IOError as e:
        print(f"An error occurred: {e}")
        return False
    
    # Post-process the file to clean it up
    try:
        # ## Step 1: Read the original, messy content from the file
        with open(output_file_path, 'r', encoding='utf-8') as file:
            raw_content = file.read()

        # ## Step 2: Remove first and last character
        cleaned_content = raw_content[1:-1]

        # Decode escape sequences like \n, \", etc.
        cleaned_content = codecs.decode(cleaned_content, 'unicode_escape')

        # ## Step 3: Overwrite the original file with the cleaned content
        with open(output_file_path, 'w', encoding='utf-8') as file:
            file.write(cleaned_content)
        
        print("✅ File has been cleaned and overwritten.")

        # ## Step 4: Parse the cleaned string and use the data
        data = json.loads(cleaned_content)
        
        # print(f"Title: {data['title']}")
        # print(f"Hint for the first path: {data['paths'][0]['hint']}")

    except FileNotFoundError:
        print(f"Error: The file at '{output_file_path}' was not found.")
        return False
    except json.JSONDecodeError as e:
        print(f"Error: The content is not valid JSON after cleaning. Details: {e}")
        return False
    except (KeyError, IndexError) as e:
        print(f"Error: The JSON is valid, but is missing an expected key or item: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

    return True

if __name__ == "__main__":
    success = generate_room_configuration()
    if success:
        print("Room configuration generated successfully.")
    else:
        print("Failed to generate room configuration.")
