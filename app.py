from flask import Flask, render_template, request
import google.generativeai as genai
import markdown2
import os
import requests
from whoosh import index
from whoosh.fields import Schema, TEXT
from whoosh.qparser import MultifieldParser
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

app = Flask(__name__, template_folder="templates", static_folder="static")

# Configure the Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Unsplash API configuration
UNSPLASH_API_KEY = os.getenv("UNSPLASH_API_KEY")
UNSPLASH_URL = "https://api.unsplash.com/search/photos"

# Paths for documents and index
DOCS_DIR = "documents"
INDEX_DIR = "indexdir"

# Create Whoosh schema for indexing documents
schema = Schema(title=TEXT(stored=True), content=TEXT)

# Create index if it does not exist
if not os.path.exists(INDEX_DIR):
    os.mkdir(INDEX_DIR)
    ix = index.create_in(INDEX_DIR, schema)
    writer = ix.writer()
    for filename in os.listdir(DOCS_DIR):
        if filename.endswith(".txt"):
            path = os.path.join(DOCS_DIR, filename)
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
                writer.add_document(title=filename, content=content)
    writer.commit()
else:
    ix = index.open_dir(INDEX_DIR)

# Function to search local documents using Whoosh
def search_documents(query, top_n=3):
    if query is None:
        raise ValueError("No query provided for document search.")
    
    with ix.searcher() as searcher:
        parser = MultifieldParser(["title", "content"], schema=ix.schema)
        myquery = parser.parse(query)
        results = searcher.search(myquery, limit=top_n)
        texts = [result['content'] for result in results]
    return "\n".join(texts)

# DuckDuckGo Search
def search_duckduckgo(query, max_results=5):
    url = "https://api.duckduckgo.com/"
    params = {
        'q': query,
        'format': 'json',
        'no_html': 1,
        'skip_disambig': 1
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()
    except Exception as e:
        print(f"Error while querying the DuckDuckGo API: {e}")
        return "", []

    texts = []
    sources = []

    # Process AbstractText and AbstractURL
    abstract = data.get('AbstractText', '')
    if abstract:
        texts.append(abstract)
        abstract_source = data.get('AbstractURL', '')
        if abstract_source:
            favicon = get_favicon(abstract_source)
            sources.append({
                'title': "Abstract",
                'url': abstract_source,
                'favicon': favicon,
                'snippet': abstract
            })

    # Process RelatedTopics for additional results
    related_topics = data.get('RelatedTopics', [])
    for topic in related_topics:
        if 'Text' in topic and 'FirstURL' in topic:
            snippet = topic.get('Text', 'No description available')
            favicon = get_favicon(topic['FirstURL'])
            sources.append({
                'title': topic['Text'],
                'url': topic['FirstURL'],
                'favicon': favicon,
                'snippet': snippet
            })
            if len(texts) >= max_results:
                break

    context = "\n".join(texts)
    formatted_sources = sources

    return context, formatted_sources

# Function to obtain a favicon for a URL
def get_favicon(url):
    try:
        domain = requests.utils.urlparse(url).netloc
        favicon_url = f"https://www.google.com/s2/favicons?sz=64&domain={domain}"
        return favicon_url
    except:
        return "https://www.google.com/s2/favicons?sz=64&domain=duckduckgo.com"

# Unsplash Search
def search_unsplash(query, per_page=5):
    headers = {
        "Authorization":"Client-ID {UNSPLASH_API_KEY}"
    }
    params = {
        "query": query,
        "per_page": per_page
    }

    try:
        response = requests.get(UNSPLASH_URL, headers=headers, params=params)
        data = response.json()
        images = [result['urls']['small'] for result in data.get('results', [])]
        return images
    except Exception as e:
        print(f"Error while querying the Unsplash API: {e}")
        return []

# Flask route
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Debugging: print form data to ensure it's being received
        print(request.form)

        # Fetch the form values
        question = request.form.get("question")  # Ensure "question" matches the HTML field
        response_type = request.form.get("response_type")

        # Debugging: Check if question is None
        if not question:
            return "No query provided", 400  # Return a 400 error for missing input

        # Search relevant information in local documents
        doc_context = search_documents(question)

        # Search relevant information in DuckDuckGo
        ddg_context, ddg_sources = search_duckduckgo(question)

        # Search images in Unsplash
        images = search_unsplash(question)

        # Combine contexts
        complete_context = f"{doc_context}\n{ddg_context}"

        # Configure response type logic
        if response_type == "simple":
            temperature = 0.5
            max_tokens = 150
            prompt = (
                f"Provide a simple answer to the following question based on the provided context.\n\n"
                f"Context:\n{complete_context}\n\n"
                f"Question: {question}\n\n"
                f"Response (in Markdown format):"
            )
        elif response_type == "moderate":
            temperature = 0.7
            max_tokens = 300
            prompt = (
                f"Provide a moderate answer to the following question based on the provided context.\n\n"
                f"Context:\n{complete_context}\n\n"
                f"Question: {question}\n\n"
                f"Response (in Markdown format):"
            )
        elif response_type == "complex":
            temperature = 0.9
            max_tokens = 600
            prompt = (
                f"Provide a detailed and explanatory answer to the following question based on the provided context.\n\n"
                f"Context:\n{complete_context}\n\n"
                f"Question: {question}\n\n"
                f"Response (in Markdown format):"
            )
        else:
            return render_template("result.html", response="Invalid response type.", sources=[], images=[])

        # Configure generation parameters
        generation_config = {
            "temperature": temperature,
            "top_p": 0.95,
            "top_k": 40,  # Updated top_k value to be within the supported range
            "max_output_tokens": max_tokens,
            "response_mime_type": "text/plain",
        }

        # Create the model
        model = genai.GenerativeModel(
            model_name="gemini-1.5-pro-002",
            generation_config=generation_config,
        )

        # Start chat session
        chat_session = model.start_chat(history=[])

        # Send message
        response = chat_session.send_message(prompt)

        # Get the generated response in Markdown format and convert to HTML
        markdown_response = response.text.strip()
        html_response = markdown2.markdown(markdown_response)

        # Use the HTML response directly without appending sources
        final_response = html_response

        return render_template("result.html", response=final_response, sources=ddg_sources, images=images)

    return render_template("index.html", response="", sources=[], images=[])


if __name__ == "__main__":
    app.run(debug=True)