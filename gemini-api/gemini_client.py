import google.generativeai as genai
import os
import json
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
gemini_api_key = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=gemini_api_key)

file_path = 'gemini-api/rooms.json'
with open(file_path, 'r') as file:
    json_data = json.load(file)

# Convert the Python dictionary to a JSON string
json_string = json.dumps(json_data, indent=2)

# generate a random theme
themes = ["alien", "pirate", "wild-west", "medieval", "robot"]
# theme = themes[random.randint(0, len(themes) - 1)]
theme = "wild-west"  # For consistency in testing
print(f"Selected theme: {theme}")

prompt = f"""
You are a creative content generator. Your task is to fill in the empty fields in the following JSON structure to create a complete story.
Choose theme of the story should be: {theme}.
The description should have enough info so that the user can solve the puzzle, but not too much that it gives away the solution.


Here is the JSON structure you need to populate:
{json_string}

Here are the constraints:
- "Title": A creative title for the story.
- "starting_description": A compelling starting point for the adventure.
- "paths": You must create 3 unique adventure paths.
- "path_name": A name for each path.
- "description": A short description of what the user will encounter on the path.
- "hint": A hint for the user on how to solve the path.
- "solution_sequence": A list of triggers to solve the path. Use the exact trigger names from the JSON.
- "audio_cue": A sound effect to play.
- "visual_effects": Two visual effects to display.
- "death_text": A creative description of what happens if the user fails.

Please generate the complete JSON object and provide only the final JSON in your response, with no additional text or explanation.
"""

model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content(prompt)

print(response.text)