# RAG-Based Multi-Video YouTube Question-Answer Assistant

## Overview

The RAG-Based Multi-Video YouTube Question-Answer Assistant is an AI-powered application that enables users to ask natural language questions across multiple YouTube videos simultaneously. The system extracts video transcripts, converts them into vector embeddings, retrieves the most relevant information using semantic search, and generates accurate, context-aware answers using Google's Gemini large language model.

This project demonstrates the implementation of Retrieval-Augmented Generation (RAG) using FastAPI, LangChain, FAISS, Hugging Face Embeddings, and Google Gemini.

---

## Features

- Upload and index multiple YouTube videos
- Automatic transcript extraction
- Intelligent text chunking for efficient retrieval
- Semantic search using vector embeddings
- AI-powered question answering
- Source-aware responses
- Persistent vector storage
- FastAPI REST API backend
- Interactive web interface built with HTML, CSS, and JavaScript
- Error handling for invalid videos and unavailable transcripts

---

## Technology Stack

### Backend

- Python
- FastAPI
- Uvicorn

### AI & Retrieval

- Google Gemini API
- LangChain
- Hugging Face Embeddings
- FAISS
- Sentence Transformers

### Frontend

- HTML5
- CSS3
- JavaScript

### Data Processing

- YouTube Transcript API
- Recursive Character Text Splitter

---

## Project Structure

```text
project/
│
├── static/
│   ├── style.css
│   ├── script.js
│
├── templates/
│   └── index.html
│
├── vectordb/
│
├── main.py
├── rag.py
├── requirements.txt
├── .env
└── README.md
```

---

## System Workflow

1. Users submit one or more YouTube video URLs.
2. The application extracts transcripts from each video.
3. The transcripts are split into smaller text chunks.
4. Each chunk is converted into vector embeddings.
5. Embeddings are stored in a FAISS vector database.
6. When a user asks a question, the query is converted into an embedding.
7. The system retrieves the most relevant transcript chunks.
8. The retrieved context is passed to Google Gemini.
9. Gemini generates a context-aware answer, which is returned along with the relevant source information.

---

## RAG Pipeline

```text
YouTube URLs
      │
      ▼
Transcript Extraction
      │
      ▼
Text Chunking
      │
      ▼
Embedding Generation
      │
      ▼
FAISS Vector Database
      │
      ▼
Semantic Retrieval
      │
      ▼
Google Gemini
      │
      ▼
Final Answer with Source References
```
