from flask import Flask, render_template, request, redirect, url_for, session, jsonify, copy_current_request_context
import os
import base64
import threading
import time
import uuid
from gemini_service import (
    get_questions_from_gemini,
    get_intro_script_from_gemini,
    get_interview_feedback_from_gemini
)
from detect_link import detect_link
from generate_avatar import generate_video

# Initialize Flask app and set configurations
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['AVATAR_FOLDER'] = 'static/videos'
app.secret_key = 'your_secret_key'

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global cache for feedback
feedback_cache = {}


@app.route('/')
def index():
    """Render the homepage."""
    return render_template('index.html')


@app.route('/generate-questions', methods=['POST'])
def generate_questions():
    """Generate questions based on the job description and other inputs."""
    job_description = request.form['job_description']
    num_questions = int(request.form['num_questions'])
    avatar = request.form['avatar']
    complexity = request.form['complexity']

    job_description = detect_link(job_description)

    # Truncate the job description if it exceeds the max length
    max_length = 2800
    if len(job_description) > max_length:
        job_description = job_description[:max_length].rstrip() + '...'

    # Fetch intro script and questions from the Gemini service
    intro_script = get_intro_script_from_gemini(job_description, num_questions, avatar)
    generated_questions = get_questions_from_gemini(job_description, num_questions, complexity, avatar)

    # Generate the intro video using the intro_script
    generate_video(intro_script, 'intro.mp4', avatar)

    # Generate videos for each question
    for idx, question in enumerate(generated_questions, start=1):
        video_name = f'question_video_{idx}.mp4'
        generate_video(question['question'], video_name, avatar)

    # Store data in session
    session['questions'] = generated_questions
    session['intro_script'] = intro_script
    session['job_description'] = job_description
    session['feedback_id'] = str(uuid.uuid4())

    return redirect(url_for('loading_screen'))


@app.route('/loading')
def loading_screen():
    """Display a loading screen while questions are generated."""
    return render_template('loading.html')


@app.route('/intro')
def intro_page():
    """Display the intro script."""
    intro_script = session.get('intro_script', "No introduction script available.")
    return render_template('intro.html', intro_script=intro_script)


@app.route('/check-intro-file')
def check_intro_file():
    """Check if the intro video file exists."""
    intro_file_path = os.path.join(app.config['AVATAR_FOLDER'], 'intro.mp4')
    file_exists = os.path.exists(intro_file_path)
    return jsonify({'exists': file_exists})


@app.route('/start-recording')
def start_recording():
    """Render the recording page with the list of questions."""
    questions = session.get('questions', [])
    print(f"Questions retrieved: {questions}")

    valid_questions = [
        question for question in questions
        if isinstance(question, dict) and 'video_path' in question and os.path.exists(question['video_path'])
    ]

    if not valid_questions:
        print("No valid questions were retrieved.")
        return render_template('error.html', message="No valid questions available. Please try again.")

    return render_template('record.html', questions=valid_questions)


@app.route('/submit-video', methods=['POST'])
def submit_video():
    """Handle video submission and save the recorded video."""
    video_data = request.form.get('video_data')

    if video_data:
        # Remove Base64 header and decode video data
        video_data = video_data.split(",")[1]
        video_bytes = base64.b64decode(video_data)

        # Save the video to a file
        video_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'recorded_interview.mp4')
        with open(video_filename, 'wb') as video_file:
            video_file.write(video_bytes)

        session['video_filename'] = video_filename
        print(f"Video saved at: {video_filename}")

    return redirect(url_for('feedback_loading'))


@app.route('/feedback-loading')
def feedback_loading():
    """Display loading screen while feedback is being processed."""
    feedback_id = session.get('feedback_id')

    if feedback_id not in feedback_cache:
        print("Starting background feedback processing...")

        @copy_current_request_context
        def process_feedback_thread():
            """Background thread for processing feedback."""
            job_description = session.get('job_description', 'No job description available')
            video_filename = session.get('video_filename')

            if video_filename:
                feedback = get_interview_feedback_from_gemini(job_description, video_filename)
                print(f"Feedback received: {feedback}")
            else:
                feedback = "No video file found for feedback."

            feedback_cache[feedback_id] = feedback

        threading.Thread(target=process_feedback_thread).start()

    return render_template('feedback_loading.html')


@app.route('/check-feedback-status')
def check_feedback_status():
    """Check if feedback is ready."""
    feedback_id = session.get('feedback_id')
    feedback = feedback_cache.get(feedback_id)

    if feedback:
        return jsonify({'status': 'done', 'feedback': feedback})

    return jsonify({'status': 'processing'})


@app.route('/feedback')
def feedback():
    """Display the feedback page."""
    feedback_id = session.get('feedback_id')
    feedback_text = feedback_cache.get(feedback_id, "No feedback available.")
    return render_template('feedback.html', feedback=feedback_text)


if __name__ == '__main__':
    app.run(debug=True)
