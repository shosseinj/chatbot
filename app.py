import os
from flask import Flask, request, jsonify, send_from_directory, session, Response, stream_with_context
from werkzeug.utils import secure_filename
from cogvault.chatbot import Chatbot, ChunkEvent, SourcesEvent, Role, Message, create_history
from cogvault.file_loader import load_uploaded_file
from langchain_ollama import ChatOllama
import time
from langchain.schema import AIMessage, HumanMessage


app = Flask(__name__)

# Configurations
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = "supersecretkey"  # Required for session handling

# Ensure necessary folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Global variable to store the chatbot instance
chatbot_instance = None

# Serve frontend files
@app.route("/")
def serve_frontend():
    return send_from_directory("frontend", "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory("frontend", path)

# def create_history(welcome_message=None):
#     """Create a chat history, optionally including a welcome message."""
#     history = []
#     if welcome_message:
#         history.append({
#             "role": welcome_message.role,  # Assuming role is a string
#             "content": welcome_message.content
#         })
#     return history

# def convert_chat_history(chat_history):
#     """Convert chat history from session format to Chatbot format."""
#     converted_history = []
#     for message in chat_history:
#         if message["role"] == "assistant":
#             converted_history.append(AIMessage(content=message["content"]))
#         elif message["role"] == "user":
#             converted_history.append(HumanMessage(content=message["content"]))
#     return converted_history
#
# converted_history = []
# def convert_chat_history(message=None):
#     """Convert chat history from session format to Chatbot format."""
#     if message is not None:
#         if message["role"] == "assistant":
#             converted_history.append(AIMessage(content=message["content"]))
#         elif message["role"] == "user":
#             converted_history.append(HumanMessage(content=message["content"]))
#     return converted_history

def initialize_chatbot(filepath):
    """Load the file and initialize the chatbot with a welcome message."""
    global chatbot_instance

    # Store the file path in the session instead of the Chatbot object
    session["filepath"] = filepath

    # Initialize the Chatbot object if not already initialized
    if chatbot_instance is None:
        chatbot_instance = Chatbot([load_uploaded_file(filepath)])

    # Define a welcome message
    welcome_message = Message(role="assistant", content="<b>Thinking...</b><br>")

    # Pass the welcome message to create_history
    session["chat_history"] = create_history(welcome_message)




@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and (file.filename.endswith('.pdf') or file.filename.endswith('.txt')):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Load file into chatbot and initialize history
        initialize_chatbot(filepath)

        return jsonify({'asset_id': filename}), 200
    else:
        return jsonify({'error': 'Invalid file type. Only PDFs are allowed.'}), 400

# @app.route('/ask', methods=['POST'])
# def ask_question():
#     # print("Route '/ask' hit")
#     if "filepath" not in session:
#         return jsonify({'error': 'No active chatbot'}), 400
#
#     # Ensure the chatbot has been initialized
#     if chatbot_instance is None:
#         return jsonify({'error': 'Chatbot is not initialized'}), 400
#
#     data = request.get_json()
#     question = data.get('question')
#
#     if not question:
#         return jsonify({'error': 'Missing question parameter'}), 400
#
#     # Get chat history from session and convert it
#     chat_history = session.get("chat_history", create_history())
#     converted_history = convert_chat_history(chat_history)
#
#     def generate_response():
#         """Generator function to stream chatbot responses."""
#         full_response = ""
#         sources = []
#         show_res = 0  # Flag to determine if thinking stage should be shown (1 means show, 0 means hide)
#         show_content = 0
#         start =0
#         inside_think_section = False  # To track if we are in the thinking section
#
#         # Collect the response and sources from the chatbot
#         for event in chatbot_instance.ask(question, converted_history):
#             if isinstance(event, ChunkEvent):
#                 content = event.content
#                 if content == '**' and start ==0:
#                     yield '<b>'
#                     start = 1
#                 if content == '**' and start == 1:
#                     yield '</b>'
#                     start= 0
#                 # Check if we're inside the <think> section
#                 if '<think>' in content:
#                     inside_think_section = True
#                 if '</think>' in content:
#                     inside_think_section = False
#                     yield "<br><br> <b>Answer:</b><br> "
#
#                 if show_res == 0:
#                     # If thinking section is enabled, yield all content (including inside <think> tags)
#                     yield f"{content}"  # Send chunk to frontend
#
#                 elif show_res == 1:
#                     # If thinking section is disabled, we only yield content after </think> is encountered
#                     if not inside_think_section:
#                         if  '\n\n' in content:
#                             yield "<br>"
#                         yield f"{content}"  # Send chunk to frontend after thinking section
#
#
#                 # print(content)  # For logging or debugging purposes
#
#             elif isinstance(event, SourcesEvent):
#                 sources = [source.page_content for source in event.content]
#
#         # Update session chat history
#         chat_history.append({"roleaccording to the user's language": "user", "content": question})
#         chat_history.append({"role": "assistant", "content": full_response})
#         session["chat_history"] = chat_history
#
#         # Send sources first, if available
#         if sources:
#             yield "<br><br><hr><br>Sources:<br>"
#
#             yield f"[{', '.join(sources)}]\n\n"
#
#         # yield " [DONE]\n\n"  # Indicate completion
#
#     return Response(stream_with_context(generate_response()), mimetype='text/event-stream')





# chat_history = create_history()

@app.route('/ask', methods=['POST'])
def ask_question():
    if "filepath" not in session:
        return jsonify({'error': 'No active chatbot'}), 400

    # Ensure the chatbot has been initialized
    if chatbot_instance is None:
        return jsonify({'error': 'Chatbot is not initialized'}), 400

    data = request.get_json()
    question = data.get('question')

    if not question:
        return jsonify({'error': 'Missing question parameter'}), 400

    # Get chat history from session
    # chat_history = session.get("chat_history", [])

    # print("Initial chat history:", chat_history)  # Debugging

    # Convert chat history to the format expected by the chatbot


    def generate_response():
        """Generator function to stream chatbot responses."""
        full_response = ""
        sources = []
        show_res = 0
        start = 0
        inside_think_section = False

        # Collect the response and sources from the chatbot
        for event in chatbot_instance.ask(question):
            if isinstance(event, ChunkEvent):
                content = event.content
                if content == '**' and start == 0:
                    yield '<b>'
                    start = 1
                if content == '**' and start == 1:
                    yield '</b>'
                    start = 0
                if '<think>' in content: 
                    inside_think_section = True
                if '</think>' in content:
                    inside_think_section = False
                    yield "<br><br> <b>Answer:</b><br> "

                if show_res == 0:
                    yield f"{content}"
                elif show_res == 1:
                    if not inside_think_section:
                        if '\n\n' in content:
                            yield "<br>"
                        yield f"{content}"

                # Accumulate the response in full_response
                # full_response += content

            elif isinstance(event, SourcesEvent):
                sources = [source.page_content for source in event.content]

        # Update session chat history
        # convert_chat_history({"role": "user", "content": question})
        # convert_chat_history({"role": "assistant", "content": full_response})


        # print("Updated chat history:", convert_chat_history())  # Debugging

        # Send sources first, if available
        if sources:
            yield "<br><br><hr><br>Sources:<br>"
            yield f"[{', '.join(sources)}]\n\n"

    return Response(stream_with_context(generate_response()), mimetype='text/event-stream')





if __name__ == '__main__':
    print("h")
    app.run(debug=True)
