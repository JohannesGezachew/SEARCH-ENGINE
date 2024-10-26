# Document Search Engine

A Flask-based web application that allows users to upload, search, and manage documents. This project demonstrates the use of text processing, search indexing, and web development with Flask.
<img width="959" alt="image" src="https://github.com/user-attachments/assets/cb8928b9-5bbc-4d8a-b585-39cedef9b39c">


## Features

- **Document Upload**: Supports uploading documents in TXT, PDF, DOC, and DOCX formats.
- **Search Functionality**: Full-text search using TF-IDF and cosine similarity.
- **Dynamic Indexing**: Automatically updates the search index with new documents.
- **User-Friendly Interface**: Responsive design with Bootstrap and custom CSS.
- **Scheduled Cleanup**: Automatically deletes old uploaded files to manage storage.
- **Logging and Error Handling**: Comprehensive logging and error handling for robust performance.

## Technologies Used

- **Flask**: Web framework for building the application.
- **NLTK**: Natural Language Toolkit for text processing.
- **Scikit-learn**: Machine learning library for TF-IDF vectorization.
- **Schedule**: Python library for scheduling periodic tasks.
- **Bootstrap**: Front-end framework for responsive design.

## Getting Started

### Prerequisites

- Python 3.x
- pip (Python package manager)

### Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/yourusername/your-repo.git
   cd your-repo
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Download NLTK data**:

   ```bash
   python download_nltk_data.py
   ```

4. **Run the application**:

   ```bash
   python app.py
   ```

5. **Access the application**: Open your browser and go to `http://localhost:5000`.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License.
