#!/bin/bash

# Variables
PROJECT_ID="YOUR_PROJECT_ID"
REGION="us-central1"
SERVICE_NAME="news-aggregator"
SCHEDULER_JOB_NAME="news-ingest-job"
API_KEY="YOUR_GEMINI_API_KEY"

# 1. Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --source . \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=$API_KEY

# Get the Service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')
echo "Service URL: $SERVICE_URL"

# 2. Create Cloud Scheduler Job (Midnight EST)
echo "Creating Cloud Scheduler Job..."
gcloud scheduler jobs create http $SCHEDULER_JOB_NAME \
  --schedule "0 0 * * *" \
  --time-zone "America/New_York" \
  --uri "$SERVICE_URL/api/batch-ingest" \
  --http-method POST \
  --location $REGION

# 3. Enable Firestore TTL
echo "Enabling Firestore TTL..."
gcloud firestore fields ttls update expire_at \
  --collection-group=articles \
  --enable-ttl

echo "Deployment setup complete!"
