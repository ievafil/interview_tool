from dotenv import load_dotenv
import os
import google.generativeai as genai
import time

# Load environment variables from .env file
load_dotenv()

# Get the Gemini API key
os.environ['KEY'] = os.getenv("GEMINI_API_KEY")

if not os.environ['KEY']:
    raise ValueError("Gemini API Key not provided. Please provide GEMINI_API_KEY as an environment variable")

# Configure the Gemini API
genai.configure(api_key=os.environ["KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

# Function to generate the intro script from the Gemini API
def get_intro_script_from_gemini(job_description, num_questions, avatar):
    """
    Generates an interview introduction script using the Gemini API.

    This function interacts with the Gemini API to create an introductory script 
    for an interview, where the interviewer (represented by an avatar) introduces 
    themselves, explains the structure of the interview, and provides instructions 
    to the candidate. It concludes by wishing the candidate good luck and prompting 
    them to start the interview recording.

    Args:
        job_description (str): The job description or link to the job posting.
        num_questions (int): The number of interview questions to be asked.
        avatar (str): The avatar or persona that will represent the interviewer.

    Returns:
        str: A generated intro script for the interview, or an error message if 
             the API request fails.

    Example Usage:
        get_intro_script_from_gemini("Software Engineer at XYZ", 5, "Sophia")
    """
    # Prepare the prompt
    prompt = (f"Can you give me an interview introduction script, please keep it short, in the first person (as the interviewer), and keep it brief."
              f" Saying, hello, I am {avatar} from the interviewing company."
              f" This interview is for the role in the job listing."
              f" Please do not leave any placeholders like [Your Name] or [Interviewer's Name] or [Company Name] in the script."
              f" You will ask {num_questions} questions, and the interview will need to be recorded to provide feedback."
              f" Ask the candidate to click the button that will come up in a second, which will take them to the interview."
              f" Advise them to start the recording straight away so the whole interview is captured."
              f" The interview questions will be in separate videos, and they should answer them chronologically, one at a time."
              f" Wish them the best of luck and say, 'Let's get started!'"
              f" If details for the script are missing, fill in appropriate and realistic values based on the job description {job_description}.")
    
    try:
        # Call the Gemini model to generate the intro script
        response = model.generate_content(prompt)
        
        # Extract the generated intro script from the response
        generated_intro_script = response.text
        return generated_intro_script

    except Exception as e:
        # Handle errors gracefully
        print(f"Error with Gemini API request: {e}")
        return "There was an error generating the intro script. Please try again later."


# Function to generate interview questions from the Gemini API
def get_questions_from_gemini(job_description, num_questions, complexity, avatar):
    """
    Generates interview questions based on the job description and complexity level using the Gemini API.

    This function generates a series of interview questions tailored to the job description and 
    the specified complexity level. It generates one fewer than the number of requested questions, 
    ensuring that the last question is always: "Do you have any questions for me?".

    Args:
        job_description (str): The job description to tailor the questions to.
        num_questions (int): The total number of questions to generate (including the final question).
        complexity (str): The complexity level of the questions (e.g., 'beginner', 'intermediate', 'complex').
        avatar (str): The interviewer.

    Returns:
        list: A list of generated interview questions and video paths, or an error message if the API request fails.

    Example Usage:
        get_questions_from_gemini("Frontend Developer at ABC", 5, "intermediate", "Matt")
    """
    # Prepare the prompt for generating interview questions
    prompt = (f"Generate a list of {num_questions - 1} interview questions. "
              f"These questions should be at a {complexity} level and should be presented as a clean list, with no extra text or introduction, or symbols. "
              f"Please ensure the final question is NOT anything related to 'Do you have any questions for me?'."
              f" The first question can be 'Tell me about yourself and why you are a good fit for this job'."
              f" Return the list with one question per line, without explanations or other commentary."
              f" Based on the following job description: {job_description}.")
    
    try:
        # Call the Gemini model to generate the interview questions
        response = model.generate_content(prompt)

        if response is None or not hasattr(response, 'text'):
            raise ValueError("Received no response or invalid response from the Gemini API.")
        
        # Split the response text into individual lines/questions
        generated_questions = response.text.strip().split("\n")

        # Filter out any empty lines and remove leading/trailing whitespace
        generated_questions = [q.strip() for q in generated_questions if q.strip()]

        # Ensure the final question is included exactly once
        final_question = "Do you have any questions for me?"

        # Remove any existing instances of the final question from the list
        if final_question in generated_questions:
            generated_questions.remove(final_question)

        # Append the final question at the end of the list
        generated_questions.append(final_question)

        # Debugging: print the generated questions
        print(f"Generated questions: {generated_questions}")

        # Generate videos for each question and return questions with video paths
        questions_with_videos = []
        for i, question in enumerate(generated_questions):
            video_filename = f"question_video_{i+1}.mp4"
            video_path = os.path.join("static/videos", video_filename)
            
            # Call the video generation function
            # generate_video_for_question(question, video_path, avatar)
            
            # Append the question and the generated video path
            questions_with_videos.append({'question': question, 'video_path': video_path})

        return questions_with_videos

    except Exception as e:
        # Handle errors gracefully
        print(f"Error generating questions: {e}")
        return ["There was an error generating the question videos. Please try again later."]


# Function to receive feedback from Gemini API on interview performance
def get_interview_feedback_from_gemini(job_description, video_file_path):
    """
    This function interacts with the Gemini API to get feedback on interview performance based on a video file.

    The feedback focuses on body language, communication, and the relevance of answers to the job description.
    
    Args:
        job_description (str): The job description to base feedback on.
        video_file_path (str): The path to the video file of the interview for analysis.

    Returns:
        str: Generated feedback or an error message.
    """
    prompt = (f"This is a test interview mp4 for the following role: {job_description}. Please provide feedback on "
              f"body language, communication skills, and the relevance of the answers to the job description. This should be a learning experience."
              f"Highlight both positive (and not so positive) aspects and areas for improvement, and how the responses could be better."
              f" Present the feedback in a way that would render well in a HTML <p></p> paragraph, no unnecessary markup, and without any html <p></p> tags.")
    
    try:
        # Upload the video file
        print(f"Uploading file: {video_file_path}...")
        video_file = genai.upload_file(path=video_file_path)
        print(f"Upload completed: {video_file.uri}")

        # Check the file's processing state
        while video_file.state.name == "PROCESSING":
            print("Processing...", end='', flush=True)
            time.sleep(10)
            video_file = genai.get_file(video_file.name)

        if video_file.state.name == "FAILED":
            raise ValueError("Video processing failed.")

        # Make the API request for feedback
        print("Requesting feedback..." + prompt)
        response = model.generate_content([video_file, prompt], request_options={"timeout": 1200})

        # Extract and return the feedback
        feedback = response.text
        return feedback

    except Exception as e:
        print(f"Error generating feedback: {e}")
        return "There was an error when requesting interview feedback. Please try again later."
