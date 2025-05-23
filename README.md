# Local Context MCP Server with RAG

Retrieves local informations with documentations, guides, and conventions, making it easy for AI assistants to access your project informations. It uses RAG (Retrieval-Augmented Generation) for semantic search capabilities and supports different document types.

This MCP (Model-Context-Protocol) server provides access to local documents stored in the `sources/` folder, making it easy for AI assistants to access your library documents.

## Features

- **Local Document Access**: Serves document files from your local `sources/` folder
- **Document Type Classification**: Automatically categorizes documents as documentation, guides, or conventions
- **Type-Based Filtering**: Search and retrieve documents by specific type
- **Semantic Search**: Find documents based on meaning, not just keywords
- **RAG Implementation**: Uses vector embeddings for document similarity and relevance ranking
- **Directory Listing**: List all available document files
- **Works Offline**: No external API calls - everything is served locally

## Installation

### Requirements

- Python 3.10+
- An MCP-compatible client (Cursor, Claude Desktop, etc.)

### Setup

1. Clone this repository or download the source code
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Make sure you have document files in the `sources/` folder (Markdown, MDX, and text files are supported)
4. Organize your documents by type:
   - **Documentation**: Technical reference material (API docs, class references, etc.)
   - **Guides**: How-to content and tutorials
   - **Conventions**: Standards, rules, and best practices

## Running the Server

Start the server with:

```bash
python docs_server.py
```

This will:
1. Create the `sources/` directory if it doesn't exist
2. Classify your documents by type (documentation, guides, conventions)
3. Build the search index from your document files
4. Start the MCP server on http://127.0.0.1:8000/mcp

## Configure Your MCP Client

### Cursor

Add the following to your Cursor `~/.cursor/mcp.json` file:

```json
{
  "mcpServers": {
    "local-docs": {
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

### Claude Desktop

Add this to your Claude Desktop `claude_desktop_config.json` file:

```json
{
  "mcpServers": {
    "local-docs": {
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

### VS Code

Add this to your VS Code MCP config file:

```json
{
  "servers": {
    "LocalDocs": {
      "type": "streamable-http",
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

## Usage

Once configured, you can use the following tools in your AI assistant:

### 1. List Local Documents

To see all available document files:

```
list_local_docs
```

This will return a list of all document files in your `sources/` folder.

### 2. List Documents by Type

To see all documents of a specific type:

```
list_docs_by_type doc_type="guide"
```

Replace "guide" with the document type you want to list ("documentation", "guide", or "convention").

### 3. Search Local Documents (Path-based)

To search for specific document files by path:

```
search_local_docs query="component"
```

Replace "component" with your search term. This will return a list of files that match your query in their path.

You can also filter by document type:

```
search_local_docs query="component" doc_type="documentation"
```

### 4. Semantic Search (Content-based)

To search for documents based on meaning and content:

```
semantic_search query="How to create a responsive layout"
```

This uses RAG to find the most relevant documents based on the semantic meaning of your query, not just keyword matching. It returns excerpts from the most relevant documents.

You can specify the maximum number of results and filter by document type:

```
semantic_search query="How to handle events" max_results=10 doc_type="guide"
```

### 5. Get Document Content

To retrieve the content of a specific document file:

```
get_local_doc file_path="app-studio/README.md"
```

Replace "app-studio/README.md" with the path to the document file you want to access. The response will include the document's content and its type.

### 6. Build Document Index

If you've added new documents or updated existing files, you can rebuild the search index:

```
build_docs_index
```

This processes all document files, classifies them by type, and creates a new search index for semantic search.

## Adding Your Own Documents

Simply add your Markdown, MDX, or text files to the `sources/` folder. The server will automatically detect, classify, and serve them.

### Document Type Classification

The server automatically classifies documents based on their content and file path:

1. **Documentation**: Technical reference material (default type if no other type is detected)
2. **Guides**: Files with "guide" in the path or title, or content that appears to be instructional
3. **Conventions**: Files with "convention" in the path or title, or content related to standards/rules

### Organization Tips

For better organization and more accurate classification:

- Use descriptive file names that indicate the document type (e.g., "api-reference.md" for documentation, "getting-started-guide.md" for guides)
- Organize files in subdirectories by type (e.g., `/sources/guides/`, `/sources/conventions/`)
- Include clear headings in your documents that indicate their purpose

## Development

### Modifying the Server

The main server code is in `docs_server.py`. After making changes, restart the server to apply them.

## License

MIT
