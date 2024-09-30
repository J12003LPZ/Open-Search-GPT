# AI-Powered Search Application

This project is an AI-driven search engine that integrates local document search, web search, and image retrieval, providing comprehensive results and AI-generated answers. Users can specify the level of detail in the responses, ranging from simple to complex.

## Features

- **Local Document Search**: Indexed using Whoosh, allowing users to search through local text documents efficiently.
- **Web Search with DuckDuckGo**: Fetches relevant web content and related topics using the DuckDuckGo API, ensuring privacy-focused search results.
- **Image Search**: Retrieves images related to the query from the Unsplash API.
- **AI-Generated Responses**: Utilizes the Gemini API to generate contextual answers based on the combined data from local documents, web search, and images. Responses are available in simple, moderate, or complex formats.
- **Technologies Used**:
  - **Backend**: Flask, Python, Whoosh (for document indexing)
  - **APIs**: Gemini for AI generation, DuckDuckGo for web search, Unsplash for images
  - **Markdown to HTML**: Converts AI responses from Markdown format to HTML for display in the frontend.

## How It Works

1. **User Input**: Users input a query and select the desired complexity of the response (simple, moderate, or complex).
2. **Document Search**: The application searches local documents indexed by Whoosh.
3. **Web and Image Search**: Simultaneously, it retrieves web content via DuckDuckGo and images from Unsplash.
4. **AI Response Generation**: Based on the gathered context, an AI-generated response is produced using the Gemini API, formatted in Markdown, and converted to HTML.
5. **Output**: The final response includes text from local documents, web results, images, and the AI-generated answer.

## Final Product

You can view the final product [here](https://open-search-gpt.vercel.app/).
