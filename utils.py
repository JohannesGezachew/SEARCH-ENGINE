import os
import chardet
import logging

logger = logging.getLogger(__name__)

def load_documents(directory):
    documents = []
    if not os.path.exists(directory):
        logger.warning(f"Directory does not exist: {directory}")
        return documents

    for filename in os.listdir(directory):
        if filename.endswith('.txt'):
            file_path = os.path.join(directory, filename)
            logger.info(f"Loading document: {file_path}")

            try:
                with open(file_path, 'rb') as raw_file:
                    raw_data = raw_file.read()
                    result = chardet.detect(raw_data)
                    encoding = result['encoding'] or 'latin-1'

                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()

                documents.append({
                    'title': filename,
                    'content': content
                })
                logger.info(f"Successfully loaded document: {filename}")

            except Exception as e:
                logger.error(f"Error loading document {filename}: {str(e)}")
                continue

    logger.info(f"Loaded {len(documents)} documents from {directory}")
    return documents
