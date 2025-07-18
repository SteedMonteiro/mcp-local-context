#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="mcp-local-context",
    version="0.1.3",
    description="Local Documentation MCP Server with RAG",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Steed Monteiro",
    author_email="steed.monteiro@gmail.com",
    url="https://github.com/steedmonteiro/mcp-local-context",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=[
        "mcp[cli]>=1.9.1",
    ],
    extras_require={
        "rag": ["vlite>=0.2.0"],
    },
    entry_points={
        "console_scripts": [
            "mcp-local-context=mcp_local_context.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
)
