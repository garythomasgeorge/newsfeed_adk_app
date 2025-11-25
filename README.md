# AI News Aggregator

A modern, AI-powered news aggregator built with the **Google Gen AI Agent Development Kit (ADK)**. The app uses a hierarchical agent architecture to scrape, analyze, and summarize news from multiple RSS feeds using Google's Gemini AI.

## Features

*   **Automated Harvesting**: Fetches news from RSS feeds (Politics, Technology, Sports, Entertainment).
*   **AI Analysis**: Uses Gemini 2.0 Flash to generate:
    *   **TL;DR Summaries**: Quick 2-3 sentence overviews.
    *   **Detailed Breakdowns**: "What Happened", "Impact", and "Conclusion".
    *   **Bias Detection**: Labels articles as Left, Lean Left, Center, Lean Right, or Right using hybrid approach (domain reputation + content analysis).
    *   **Topic Tagging**: Automatically categorizes content.
    *   **Keyword Extraction**: Identifies key entities (people, places, organizations).
*   **ADK Agent Architecture**:
    *   **NewsChiefAgent** (Root): Orchestrates the entire news workflow.
    *   **HarvesterAgent**: Fast collection of raw articles from RSS feeds.
    *   **AnalystAgent**: Background processing for deep analysis and summarization.
    *   **LibrarianAgent**: Natural language search query translation.
*   **Modern UI**:
    *   Clean, responsive React frontend with card-based design.
    *   Dark mode support.
    *   **Bias Meter**: Visual indicator of article bias on every card.
    *   **Date Filtering**: Calendar view to browse past news.
    *   **Similar Sources**: Find coverage from other outlets for the same story.
    *   **Enhanced Article View**: Card-based layout with section dividers and icons.

## Architecture

The system is built with the **Google ADK framework** using a hierarchical agent architecture for scalability and modularity.

*   **Backend**: Python (FastAPI) + Google ADK
*   **Frontend**: React (Vite)
*   **Database**: Google Cloud Firestore
*   **AI Engine**: Google Gemini API (via ADK)
*   **Agent Framework**: Google Gen AI Agent Development Kit (ADK)
*   **Task Queue**: Python `asyncio` background tasks (can be scaled to Cloud Tasks).

## Setup Instructions

### Prerequisites

*   Python 3.10+ (recommended for full ADK support, 3.9+ minimum)
*   Node.js 16+
*   Google Cloud Project with Firestore enabled.
*   Gemini API Key.

### 1. Clone the Repository

```bash
git clone <repository-url>
cd newsfeed_adk_app
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in `backend/`:

```env
GOOGLE_API_KEY=your_gemini_api_key
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account.json
PROJECT_ID=your_gcp_project_id
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

### 4. Run Locally

Use the provided startup script to run both backend and frontend:

```bash
./start_local.sh
```

*   Frontend: `http://localhost:5173`
*   Backend API: `http://localhost:8080`
*   API Docs: `http://localhost:8080/docs`

## API Endpoints

*   `POST /api/batch-ingest`: Triggers the **NewsChiefAgent** to orchestrate news harvesting and analysis.
*   `POST /api/process-queue`: Triggers the **AnalystAgent** to process pending articles.
*   `POST /api/process-backfill`: Force-processes older articles.
*   `GET /api/feed`: Retrieves the latest news feed.
*   `GET /api/available-dates`: Returns dates with available news.
*   `GET /api/articles/similar`: Finds related articles.
*   `POST /api/search`: Natural language search (powered by **LibrarianAgent**).

## Deployment

The application is containerized using Docker and designed for Google Cloud Run.

```bash
# Build and Deploy
gcloud run deploy news-aggregator --source .
```

See `deploy_commands.sh` for detailed deployment steps, including setting up Cloud Scheduler for daily ingestion.
