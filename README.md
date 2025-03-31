# Web Search Agent

A powerful AI-powered web search agent that combines web crawling, vectorized database storage, and LLM processing to provide intelligent search capabilities.

## Features

- 🌐 Web Search Integration: Uses DuckDuckGo for initial search results
- 🤖 Web Crawler: Async web crawler with content filtering and markdown generation
- 🧠 LLM Processing: Uses Groq LLM for processing queries and generating responses
- 📊 Vectorized Database: Uses Pinecone for storing and retrieving contextual information
- 🎨 User-Friendly Interface: Built with Streamlit for an intuitive web interface

## Setup

1. Clone the repository:
```bash
git clone [repository-url]
cd web-search-agent-v0
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables in a `.env` file:
```bash
GROQ_API_KEY="your_groq_api_key"
PINECONE_API_KEY="your_pinecone_api_key"
PINECONE_INDEX_NAME="your_pinecone_index_name"
```

4. Run the application:
```bash
streamlit run app.py
```

## Usage

1. Open the application in your browser.
2. Enter your query in the text area.
3. Toggle the "Enable web search" option if you want to perform a web search.
4. Click the "⚡️ Go" button to process your query.

## Notes
- The web crawler will fetch and process up to 10 web pages for each search.
- The vectorized database will store contextual information for up to 1000 chunks of text.
- The LLM will process the context and generate a response based on the query.


## Tech Stack
- Python
- Streamlit
- Groq
- Pinecone
- Crawl4AI
- DuckDuckGo Search
- Ollama
- LangChain