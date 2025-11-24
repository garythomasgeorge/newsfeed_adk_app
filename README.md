# AI News Aggregator

A modern, AI-powered news aggregator that scrapes, analyzes, and summarizes news from multiple RSS feeds. It uses Google's Gemini AI to generate structured summaries, detect bias, and tag articles.

## Features

*   **Automated Harvesting**: Fetches news from RSS feeds (Politics, Technology, Sports, Entertainment).
*   **AI Analysis**: Uses Gemini 1.5 Flash to generate:
    *   **TL;DR Summaries**: Quick 2-3 sentence overviews.
    *   **Detailed Breakdowns**: "What Happened", "Impact", and "Conclusion".
    *   **Bias Detection**: Labels articles as Left, Center, or Right.
    *   **Topic Tagging**: Automatically categorizes content.
*   **Split-Brain Architecture**:
    *   **Harvester**: Fast collection of raw articles.
    *   **Analyst**: Background processing for deep analysis.
    *   **Librarian**: Natural language search and retrieval.
*   **Modern UI**:
    *   Clean, responsive React frontend.
    *   Dark mode support.
    *   **Bias Meter**: Visual indicator of article bias.
    *   **Date Filtering**: Calendar view to browse past news.
    *   **Similar Sources**: Find coverage from other outlets for the same story.

## Architecture

The system is built with a decoupled architecture to ensure scalability and performance.

*   **Backend**: Python (FastAPI)
*   **Frontend**: React (Vite)
*   **Database**: Google Cloud Firestore
*   **AI Engine**: Google Gemini API
*   **Task Queue**: Python `asyncio` background tasks (can be scaled to Cloud Tasks).

## Setup Instructions

### Prerequisites

*   Python 3.9+
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

*   `POST /api/batch-ingest`: Triggers the Harvester to fetch new articles.
*   `POST /api/process-queue`: Triggers the Analyst to process pending articles.
*   `POST /api/process-backfill`: Force-processes older articles.
*   `GET /api/feed`: Retrieves the latest news feed.
*   `GET /api/available-dates`: Returns dates with available news.
*   `GET /api/articles/similar`: Finds related articles.
*   `POST /api/search`: Natural language search.

## Deployment

The application is containerized using Docker and designed for Google Cloud Run.

```bash
# Build and Deploy
gcloud run deploy news-aggregator --source .
```

See `deploy_commands.sh` for detailed deployment steps, including setting up Cloud Scheduler for daily ingestion.
