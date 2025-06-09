# RBI Circulars AI Assistant

This project is an intelligent search and query engine for RBI circulars, built with Streamlit, Qdrant, and Google's Gemini API. It uses a Retrieval-Augmented Generation (RAG) architecture to provide accurate, context-aware answers to natural language questions.

## Project Structure

```
rbi-rag-engine/
├── data/
│   └── rbi_circulars.json
├── src/
│   ├── ingestion/
│   │   └── ingest.py
│   ├── retrieval/
│   │   └── rag.py
│   └── utils/
│       └── config.py
├── .env
├── .gitignore
├── app.py
├── docker-compose.yml
├── Dockerfile
├── README.md
└── requirements.txt
```

## How to Run

### Prerequisites
- Docker
- Docker Compose

### Step 1: Clone or Create the Project
Create the project directory and all the necessary files as described in the structure above.

### Step 2: Add Your API Key
Open the `.env` file and replace the placeholder with your actual Google Gemini API key.
```env
GOOGLE_API_KEY="YOUR_GEMINI_API_KEY_HERE"
```

### Step 3: Add the Data
Place the `rbi_circulars.json` file inside the `data/` directory.

### Step 4: Build and Start the Services
Open a terminal in the project's root directory (`rbi-rag-engine/`) and run the following command. This will build the Streamlit application container and start both the Qdrant database and the app.

```bash
docker-compose up --build
```
Wait for the logs to show that both `qdrant_db` and `rag_app` are running.

### Step 5: Run the Data Ingestion (One-Time Step)
This step loads the RBI circular data into the Qdrant vector database.

Open a **new terminal window** and run this command:
```bash
docker-compose exec app python -m src.ingestion.ingest
```
You will see progress messages in the terminal. This process may take a minute or two to complete.

### Step 6: Access the Application
Open your web browser and navigate to:
**[http://localhost:8501](http://localhost:8501)**

You can now start asking questions!

### Example Questions:
- "What are the guidelines for Government Debt Relief Schemes?"
- "Tell me about the name look-up facility for RTGS."
- "What is the deadline for banks to implement the NEFT name look-up?" 