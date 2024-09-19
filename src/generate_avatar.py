import requests
import time
import os
import json
import base64
from dotenv import load_dotenv

def generate_video(input_text, video_name, avatar):
    """
    Generate a video of an avatar speaking the given input text.

    Args:
        input_text (str): The text that the avatar will speak.
        video_name (str): The name of the output video file.
        avatar (str): The name of the avatar to use ('sophia', 'diana', or 'matt').

    Raises:
        ValueError: If the API key is not set or an invalid avatar is chosen.

    Returns:
        None
    """
    # Load environment variables from .env file
    load_dotenv()

    # Get the D-ID API key from environment variables
    api_key = os.getenv("DID_API_KEY")

    if not api_key:
        raise ValueError("DID_API_KEY is not set in the environment.")

    # Base URL for the D-ID API
    base_url = 'https://api.d-id.com'

    # Encode the API key for the Authorization header
    auth_string = f'{api_key}:'
    auth_bytes = auth_string.encode('ascii')
    auth_base64 = base64.b64encode(auth_bytes).decode('ascii')

    # Headers with correct Authorization format
    headers = {
        'Authorization': f'Basic {auth_base64}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    # Convert avatar to lowercase to ensure case-insensitive matching
    avatar_lower = avatar.lower()

    if 'sophia' in avatar_lower:
        avatar_id = 'sophia-ndjDZ_Osqg'
        voice_id = 'en-US-ElizabethNeural'
    elif 'diana' in avatar_lower:
        avatar_id = 'diana-tfTP6K9S9u'
        voice_id = 'en-US-CoraNeural'
    elif 'matt' in avatar_lower:
        avatar_id = 'matt-PEvEohn_gk'
        voice_id = 'en-US-TonyNeural'
    else:
        raise ValueError('Invalid avatar chosen')

    # Payload for creating the clip
    payload = {
        'script': {
            'type': 'text',
            'input': input_text  # The text you want the avatar to speak
        },
        'presenter_id': avatar_id,  # The ID of the selected avatar
        'background': {
            'source_url': 'https://upload.wikimedia.org/wikipedia/commons/2/22/Large_meeting_room_%28Unsplash%29.jpg'
        }
    }

    # Specify voice parameters
    payload['script']['provider'] = {
        'type': 'microsoft',
        'voice_id': voice_id,
        'voice_config': {
            'style': 'Cheerful'
        }
    }

    # Step 1: Create the clip
    create_clip_url = f'{base_url}/clips'
    response = requests.post(create_clip_url, json=payload, headers=headers)

    if response.status_code == 201:
        # Clip creation initiated successfully
        response_data = response.json()
        clip_id = response_data.get('id')

        if clip_id:
            # Step 2: Poll for the clip status
            result_url = None
            status = ''
            while status != 'done':
                time.sleep(5)  # Wait for 5 seconds before checking again
                status_response = requests.get(f'{create_clip_url}/{clip_id}', headers=headers)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data.get('status')

                    if status == 'done':
                        result_url = status_data.get('result_url')
                        break
                    elif status == 'error':
                        print('Error generating clip:', status_data.get('error'))
                        break
                else:
                    print('Error checking clip status:', status_response.text)
                    break

            if result_url:
                # Step 3: Download the video
                video_response = requests.get(result_url)

                if video_response.status_code == 200:
                    # Get the directory of the current script
                    script_dir = os.path.dirname(os.path.abspath(__file__))

                    # Define the path to the 'static/videos' folder
                    videos_dir = os.path.join(script_dir, 'static', 'videos')

                    # Ensure the 'static/videos' directory exists
                    os.makedirs(videos_dir, exist_ok=True)

                    # Define the path for the video file
                    video_path = os.path.join(videos_dir, video_name)

                    # Save the video to the specified path
                    with open(video_path, 'wb') as video_file:
                        video_file.write(video_response.content)
                    print(f'Video downloaded and saved successfully as {video_path}')
                else:
                    print('Failed to download the video. Status code:', video_response.status_code)
            else:
                print('Failed to retrieve the video URL.')
        else:
            print('Failed to get clip ID from the response.')
    else:
        print('Error initiating clip creation:', response.text)
