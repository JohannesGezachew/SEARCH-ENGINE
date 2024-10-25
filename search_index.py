import json
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from sklearn.metrics.pairwise import cosine_similarity
import os
import string
import numpy as np
import logging
from scipy.sparse import vstack
import pickle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the stemmer and stop words
stemmer = PorterStemmer()
stop_words = set(stopwords.words('english'))

# Initialize the documents list
documents = []

def preprocess(text):
    # Tokenize and stem the text
    tokens = word_tokenize(text.lower())
    tokens = [token for token in tokens if token not in string.punctuation]
    stemmed_tokens = [stemmer.stem(token) for token in tokens if token not in stop_words]
    return stemmed_tokens

def create_index(documents):
    logger.info(f"Creating index for {len(documents)} documents")
    inverted_index = {}
    doc_texts = []

    for doc_id, doc in enumerate(documents):
        try:
            tokens = preprocess(doc['content'])
            for token in tokens:
                if token not in inverted_index:
                    inverted_index[token] = []
                inverted_index[token].append(doc_id)
            doc_texts.append(' '.join(tokens))
            logger.debug(f"Processed document {doc_id}: {doc['title']}")
        except Exception as e:
            logger.error(f"Error processing document {doc_id}: {str(e)}")
            continue

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(doc_texts)
    logger.info("Index creation completed")
    logger.info(f"TF-IDF matrix shape: {tfidf_matrix.shape}")

    return inverted_index, vectorizer, tfidf_matrix

def add_document_to_index(document, doc_id, inverted_index, vectorizer, tfidf_matrix):
    tokens = preprocess(document['content'])
    for token in tokens:
        if token not in inverted_index:
            inverted_index[token] = []
        inverted_index[token].append(doc_id)

    doc_text = ' '.join(tokens)
    new_vector = vectorizer.transform([doc_text])
    tfidf_matrix = vstack([tfidf_matrix, new_vector])

    return inverted_index, tfidf_matrix

def create_snippet(text, query_tokens):
    words = text.split()
    query_words = set(query_tokens)
    snippet_size = 100  # Define the size of the snippet
    snippet = []

    for i, word in enumerate(words):
        if stemmer.stem(word.lower()) in query_words:
            start = max(0, i - snippet_size // 2)
            end = min(len(words), i + snippet_size // 2)
            snippet = words[start:end]
            break

    highlighted_snippet = ' '.join(
        [f"<mark>{w}</mark>" if stemmer.stem(w.lower()) in query_words else w for w in snippet])
    return '... ' + highlighted_snippet + ' ...'

def search(query, inverted_index, vectorizer, tfidf_matrix, documents):
    logger.info(f"Searching for query: {query}")

    if not query or not documents or not inverted_index or tfidf_matrix is None:
        logger.warning("Missing required components for search")
        return []

    query_tokens = preprocess(query)
    if not query_tokens:
        logger.warning("No valid tokens in query after preprocessing")
        return []

    try:
        # Find relevant documents
        relevant_docs = set()
        for token in query_tokens:
            if token in inverted_index:
                # Ensure document IDs are valid
                valid_docs = [doc_id for doc_id in inverted_index[token] if doc_id < len(documents)]
                relevant_docs.update(valid_docs)

        if not relevant_docs:
            logger.info("No relevant documents found")
            return []

        # Convert to list and sort for consistent ordering
        relevant_docs = sorted(list(relevant_docs))

        # Check if relevant_docs indices are within the bounds of the TF-IDF matrix
        max_index = tfidf_matrix.shape[0] - 1
        relevant_docs = [doc_id for doc_id in relevant_docs if doc_id <= max_index]

        if not relevant_docs:
            logger.info("No relevant documents found after filtering")
            return []

        # Create query vector
        query_vector = vectorizer.transform([' '.join(query_tokens)])

        # Get document vectors for relevant docs only
        doc_vectors = tfidf_matrix[relevant_docs]

        if doc_vectors.shape[0] == 0:
            logger.info("No document vectors found for the query")
            return []

        # Calculate similarities
        scores = cosine_similarity(doc_vectors, query_vector).flatten()

        # Create results
        results = []
        for doc_idx, score in zip(relevant_docs, scores):
            if score > 0:
                doc = documents[doc_idx]
                snippet = create_snippet(doc['content'], query_tokens)
                results.append({
                    "title": doc["title"],
                    "snippet": snippet,
                    "score": float(score)
                })

        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)
        logger.info(f"Found {len(results)} results")
        return results

    except Exception as e:
        logger.error(f"Error during search: {str(e)}", exc_info=True)
        return []

def add_uploaded_documents(uploaded_documents, inverted_index, vectorizer, tfidf_matrix):
    global documents  # Explicitly declare we're using the global documents list

    start_doc_id = len(documents)  # Get the starting document ID

    for i, document in enumerate(uploaded_documents):
        doc_id = start_doc_id + i  # Calculate the correct document ID
        logger.info(f"Adding document ID {doc_id}: {document['title']}")

        # Add document to the documents list first
        documents.append(document)

        # Then update the index
        inverted_index, tfidf_matrix = add_document_to_index(document, doc_id, inverted_index, vectorizer, tfidf_matrix)
        logger.debug(f"Document {doc_id} added to inverted_index and tfidf_matrix")

    # Re-fit the vectorizer with all documents
    logger.info("Re-fitting the vectorizer with all documents to include new terms.")
    doc_texts = [' '.join(preprocess(doc['content'])) for doc in documents]
    vectorizer.fit(doc_texts)

    # Recreate the tfidf_matrix for all documents
    logger.info("Recreating the TF-IDF matrix with the updated vectorizer.")
    tfidf_matrix = vectorizer.transform(doc_texts)

    logger.info(f"Added {len(uploaded_documents)} documents to the index and updated the vectorizer.")
    logger.debug(f"Current number of documents: {len(documents)}")
    logger.debug(f"TF-IDF matrix shape: {tfidf_matrix.shape}")

    return inverted_index, tfidf_matrix, vectorizer

def save_index(inverted_index, vectorizer, tfidf_matrix, filepath='index_data.pkl'):
    with open(filepath, 'wb') as f:
        pickle.dump({
            'inverted_index': inverted_index,
            'vectorizer': vectorizer,
            'tfidf_matrix': tfidf_matrix,
            'documents': documents  # Ensure documents are also saved
        }, f)
    logger.info("Index data saved successfully")

def load_index(filepath='index_data.pkl'):
    if not os.path.exists(filepath):
        logger.warning(f"Index file {filepath} does not exist. Creating a new index.")
        return None, None, None, []  # Return empty list instead of None for documents
    with open(filepath, 'rb') as f:
        data = pickle.load(f)
    global documents
    documents = data.get('documents', [])
    return data['inverted_index'], data['vectorizer'], data['tfidf_matrix'], documents

def validate_documents(documents):
    validated = []
    for doc in documents:
        if 'title' in doc and 'content' in doc:
            validated.append(doc)
        else:
            logger.warning(f"Document missing 'title' or 'content': {doc}")
    return validated

if __name__ == "__main__":
    # Initialize or load the index
    inverted_index, vectorizer, tfidf_matrix, documents = load_index()

    if inverted_index is None:
        # If no existing index, initialize with initial documents
        initial_documents = [
            {"title": "Existing Document 1", "content": "Content of the existing document 1."},
            {"title": "Existing Document 2", "content": "Content of the existing document 2."}
        ]
        initial_documents = validate_documents(initial_documents)
        documents.extend(initial_documents)
        inverted_index, vectorizer, tfidf_matrix = create_index(documents)
        save_index(inverted_index, vectorizer, tfidf_matrix)
    else:
        logger.info(f"Loaded {len(documents)} existing documents from the index.")

    # Example usage after uploading documents
    uploaded_docs = [
        {"title": "New Document 1", "content": "Content of the new document 1."},
        {"title": "New Document 2", "content": "Content of the new document 2."}
    ]

    uploaded_docs = validate_documents(uploaded_docs)
    inverted_index, tfidf_matrix, vectorizer = add_uploaded_documents(uploaded_docs, inverted_index, vectorizer, tfidf_matrix)
    save_index(inverted_index, vectorizer, tfidf_matrix)  # Save after adding new documents

    logger.debug(f"Current number of documents: {len(documents)}")
    logger.info(f"TF-IDF matrix shape: {tfidf_matrix.shape}")
    logger.info(f"Total documents after upload: {len(documents)}")

    test_query = "specific term from uploaded document"
    search_results = search(test_query, inverted_index, vectorizer, tfidf_matrix, documents)
    logger.info(f"Search results for '{test_query}': {search_results}")
