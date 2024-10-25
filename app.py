from flask import Flask, request, render_template, redirect, url_for, jsonify
from search_index import (
    create_index,
    search,
    add_document_to_index,
    add_uploaded_documents,
    save_index,
    load_index,
    validate_documents,
    preprocess  # Import preprocess from search_index
)
from utils import load_documents
from werkzeug.utils import secure_filename
import os
import chardet
import logging
# from text_utils import preprocess
import time
import schedule
from datetime import datetime, timedelta

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration for file uploads
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB limit

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Add these at the top of the file after Flask initialization
documents = []
uploaded_documents = []
all_documents = []
inverted_index = None
vectorizer = None
tfidf_matrix = None

def reload_documents():
    global documents, uploaded_documents, all_documents, inverted_index, vectorizer, tfidf_matrix
    # Load documents
    documents = load_documents('doc')  # Ensure this directory exists and contains documents
    uploaded_documents = load_documents(UPLOAD_FOLDER)  # Ensure this directory is correct
    all_documents = documents + uploaded_documents
    # Create index
    inverted_index, vectorizer, tfidf_matrix = create_index(all_documents)
    documents = all_documents  # Update the global documents list

# Initial load
reload_documents()

def delete_old_files(directory, age_in_seconds):
    now = time.time()
    logger.info(f"Running cleanup for directory: {directory}")
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            file_age = now - os.path.getmtime(file_path)
            logger.debug(f"Checking file: {file_path}, age: {file_age} seconds")
            if file_age > age_in_seconds:
                try:
                    os.remove(file_path)
                    logger.info(f"Deleted old file: {file_path}")
                except Exception as e:
                    logger.error(f"Error deleting file {file_path}: {str(e)}")

# Schedule the cleanup task
def schedule_cleanup():
    logger.info("Scheduling cleanup task")
    schedule.every(1).hour.do(delete_old_files, UPLOAD_FOLDER, 600)  # Delete files older than 1 hour

# Run the scheduled tasks
def run_scheduled_tasks():
    logger.info("Starting scheduled tasks")
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

# Start the scheduled tasks in a separate thread
import threading
cleanup_thread = threading.Thread(target=run_scheduled_tasks)
cleanup_thread.start()

@app.route('/', methods=['GET', 'POST'])
def search_page():
    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        logger.info(f"Received search query: {query}")

        if not query:
            return render_template('search.html', error="Please enter a search query")

        try:
            results = search(query, inverted_index, vectorizer, tfidf_matrix, all_documents)
            logger.info(f"Found {len(results)} results")
            return render_template('search_results.html', query=query, results=results)
        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            return render_template('search.html', error="An error occurred while searching. Please try again.")

    return render_template('search.html')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            logger.error("No file part in request")
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            logger.error("No selected file")
            return redirect(request.url)

        if file and allowed_file(file.filename):
            try:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                # Read the file content
                content = file.read()

                # Try to decode the content
                try:
                    encoding = chardet.detect(content)['encoding']
                    if not encoding:
                        encoding = 'latin-1'
                    text_content = content.decode(encoding)
                except UnicodeDecodeError:
                    text_content = content.decode('latin-1')

                # Save the file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text_content)

                logger.info(f"File saved successfully: {filename}")

                # Reload all documents and recreate index
                reload_documents()

                logger.info(f"Documents reloaded and index recreated")
                return redirect(url_for('search_page'))

            except Exception as e:
                logger.error(f"Error processing file: {str(e)}")
                return f"Error processing file: {str(e)}", 500

    return render_template('upload.html')

# Example search query
query = "new document"

# Perform search
results = search(query, inverted_index, vectorizer, tfidf_matrix, documents)
for result in results:
    print(f"Title: {result['title']}")
    print(f"Snippet: {result['snippet']}")
    print(f"Score: {result['score']}\n")

# Example: Upload new documents
uploaded_docs = [
    {"title": "New Document 1", "content": "Content of the new document 1."},
    {"title": "New Document 2", "content": "Content of the new document 2."}
]

# Validate and add uploaded documents
uploaded_docs = validate_documents(uploaded_docs)
# Modify the unpacking to include the vectorizer
inverted_index, tfidf_matrix, vectorizer = add_uploaded_documents(uploaded_docs, inverted_index, vectorizer, tfidf_matrix)

# Save the updated index
save_index(inverted_index, vectorizer, tfidf_matrix)

print(f"Updated number of documents: {len(documents)}")

for doc in documents[:5]:  # Check the first 5 documents
    logger.debug(f"Document title: {doc['title']}, content snippet: {doc['content'][:100]}")

logger.info(f"Inverted index size: {len(inverted_index)}")

logger.info(f"TF-IDF matrix shape: {tfidf_matrix.shape}")

if __name__ == '__main__':
    app.run(debug=True)
