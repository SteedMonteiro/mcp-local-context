#!/bin/bash

# MCP Local Context Installer
# This script installs and sets up the MCP Local Context server

# Function to display help
show_help() {
    echo "MCP Local Context Installer"
    echo ""
    echo "Usage: ./install.sh [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help                 Show this help message"
    echo "  -i, --install              Install dependencies"
    echo "  -r, --run [source_dirs]    Run the server with specified source directories"
    echo "                             (default: sources)"
    echo "  -a, --all [source_dirs]    Install dependencies and run the server"
    echo "                             (default: sources)"
    echo "  -p, --publish [bump_type]  Publish package to PyPI with version bump"
    echo "                             (bump_type: major, minor, patch - default: patch)"
    echo "  --host [hostname]          Host to run the server on (default: 127.0.0.1)"
    echo "  --port [port]              Port to run the server on (default: 8000)"
    echo "  --path [path]              Path for the MCP endpoint (default: /mcp)"
    echo ""
    echo "Examples:"
    echo "  ./install.sh --install                  # Install dependencies"
    echo "  ./install.sh --run                      # Run with default 'sources' directory"
    echo "  ./install.sh --run docs api-docs specs  # Run with multiple source directories"
    echo "  ./install.sh --all                      # Install and run with default 'sources' directory"
    echo "  ./install.sh --all docs api-docs        # Install and run with multiple source directories"
    echo "  ./install.sh --all --host 0.0.0.0       # Install and run with custom host"
    echo "  ./install.sh --publish                  # Publish with patch version bump"
    echo "  ./install.sh --publish minor            # Publish with minor version bump"
    echo ""
}

# Function to install dependencies
install_deps() {
    echo "Installing dependencies..."
    if command -v uv &> /dev/null; then
        echo "Using uv to install dependencies..."
        uv pip install -e .
    else
        echo "Using pip to install dependencies..."
        pip install -e .
    fi
    echo "Dependencies installed successfully!"
}

# Function to run the server
run_server() {
    local sources=("$@")
    local host_arg=""
    local port_arg=""
    local path_arg=""

    # Extract host, port, and path arguments if present
    local i=0
    for arg in "${sources[@]}"; do
        if [[ "$arg" == "--host" ]]; then
            host_arg="$arg ${sources[$(($i+1))]}"
            export MCP_HOST="${sources[$(($i+1))]}"
            unset sources[$i]
            unset sources[$(($i+1))]
        elif [[ "$arg" == "--port" ]]; then
            port_arg="$arg ${sources[$(($i+1))]}"
            export MCP_PORT="${sources[$(($i+1))]}"
            unset sources[$i]
            unset sources[$(($i+1))]
        elif [[ "$arg" == "--path" ]]; then
            path_arg="$arg ${sources[$(($i+1))]}"
            export MCP_PATH="${sources[$(($i+1))]}"
            unset sources[$i]
            unset sources[$(($i+1))]
        fi
        i=$((i+1))
    done

    # If no sources provided, use default
    if [ ${#sources[@]} -eq 0 ]; then
        sources=("sources")
    fi

    # Build the sources argument and environment variable
    local sources_arg=""
    local sources_env=""
    for src in "${sources[@]}"; do
        # Skip if it's an empty element (from unset)
        if [ -n "$src" ]; then
            sources_arg="$sources_arg --sources $src"
            if [ -z "$sources_env" ]; then
                sources_env="$src"
            else
                sources_env="$sources_env,$src"
            fi
        fi
    done

    # Set environment variable for sources
    export SOURCE_DIRS="$sources_env"

    echo "Starting MCP Local Context server with sources: ${sources[*]}"
    python docs_server.py $sources_arg $host_arg $port_arg $path_arg
}

# Function to install and run
install_and_run() {
    install_deps
    run_server "$@"
}

# Function to publish package
publish_package() {
    local bump_type="${1:-patch}"

    # Validate bump type
    if [[ "$bump_type" != "major" && "$bump_type" != "minor" && "$bump_type" != "patch" ]]; then
        echo "Invalid bump type. Use 'major', 'minor', or 'patch'."
        exit 1
    fi

    echo "Publishing package with $bump_type version bump..."

    # Check if publish.sh exists and is executable
    if [ ! -f "publish.sh" ]; then
        echo "Error: publish.sh not found!"
        exit 1
    fi

    if [ ! -x "publish.sh" ]; then
        echo "Making publish.sh executable..."
        chmod +x publish.sh
    fi

    # Run the publish script
    ./publish.sh "$bump_type"
}

# Parse command line arguments
if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

case "$1" in
    -h|--help)
        show_help
        ;;
    -i|--install)
        install_deps
        ;;
    -r|--run)
        shift
        run_server "$@"
        ;;
    -a|--all)
        shift
        install_and_run "$@"
        ;;
    -p|--publish)
        shift
        publish_package "$@"
        ;;
    *)
        echo "Unknown option: $1"
        show_help
        exit 1
        ;;
esac
