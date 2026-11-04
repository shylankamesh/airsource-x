# Deploy AirSource X to Google Cloud Run

The Streamlit app is packaged for Cloud Run and reads the platform-provided `PORT`. Deployment requires a Google Cloud project with billing enabled and an account allowed to deploy Cloud Run services.

## Deploy from Google Cloud Shell

1. Enable 2-Step Verification on the Google account if Google requires it, then select the trial project in the Cloud Console.
2. Open [Google Cloud Shell](https://console.cloud.google.com/?cloudshell=true) for that project and clone the V8 source from the public `main` branch:

   ```bash
   git clone https://github.com/shylankamesh/airsource-x.git airsource-x-v8
   cd airsource-x-v8
   ```

3. Deploy the source as a public Cloud Run service (the app contains historical, public research data and no user accounts):

   ```bash
   gcloud run deploy airsource-x \
     --source . \
     --region asia-south1 \
     --allow-unauthenticated \
     --memory 2Gi \
     --cpu 2 \
     --timeout 300
   ```

4. Choose `Y` if prompted to enable required APIs or create an Artifact Registry repository. Copy the service URL printed when deployment finishes.
5. Open the URL in a private/incognito browser window. Confirm the overview loads, select **Forecast lab**, and confirm the bundled historical model preview appears. Check that the page identifies the data as historical (June 2018–October 2019).
6. Add the verified URL and screenshots of the running app to the README before submitting.

Google Cloud Run source deployment builds the project using buildpacks; the included Dockerfile is available for deployments using a container build. Keep the service public only if the team intends judges to access the demo without authentication. Review Cloud Billing after the hackathon and delete the service if it is no longer needed.

## Limits

The public demo is a research prototype. It does not provide current station observations or official AQI, health advice, or validated source attribution. The current-context mode calls Open-Meteo when used and needs outbound internet access.

## Official references

- [Deploy a Python Streamlit service to Cloud Run](https://docs.cloud.google.com/run/docs/quickstarts/build-and-deploy/deploy-python-streamlit-service)
- [Allow public access to a Cloud Run service](https://docs.cloud.google.com/run/docs/authenticating/public)
