# Deploy AirSource X to Google Cloud Run

The Streamlit app is packaged for Cloud Run and reads the platform-provided `PORT`. Deployment requires a Google Cloud project with billing enabled and an account allowed to deploy Cloud Run services.

## Deploy from Google Cloud Shell

1. Select the intended trial project in the Cloud Console and open [Google Cloud Shell](https://console.cloud.google.com/?cloudshell=true).
2. Get the current public V8 source. For a fresh clone:

   ```bash
   git clone https://github.com/shylankamesh/airsource-x.git airsource-x-v8
   cd airsource-x-v8
   ```

   If `airsource-x-v8` already exists, update it instead:

   ```bash
   cd ~/airsource-x-v8
   git pull origin main
   ```

3. Confirm the `Dockerfile` is in this directory. It installs `libgomp1`, required by the bundled LightGBM model artifacts. Deploy from this directory so Cloud Run uses that Dockerfile:

   ```bash
   gcloud run deploy airsource-x \
     --source . \
     --region asia-south1 \
     --allow-unauthenticated \
     --memory 2Gi \
     --cpu 2 \
     --timeout 300
   ```

4. Choose `Y` if prompted to enable required APIs or create an Artifact Registry repository. Wait for deployment to finish and copy the service URL.
5. Open the URL in a private/incognito browser window. Confirm the overview loads, select **Forecast lab**, and confirm both bundled historical model horizons appear without an error. Check that the page identifies the data as historical (June 2018–October 2019).
6. Only after that verification, add the public URL and screenshots of the running app to the README.

Cloud Run uses the Dockerfile when one is present in the selected source directory; if the build output says it is using buildpacks, stop and check that you are in the repository root and that `Dockerfile` exists there. Keep the service public only if the team intends judges to access the demo without authentication. Review Cloud Billing after the hackathon and delete the service if it is no longer needed.

## Limits

The public demo is a research prototype. It does not provide current station observations or official AQI, health advice, or validated source attribution. The current-context mode calls Open-Meteo when used and needs outbound internet access.

## Official references

- [Deploy a Python Streamlit service to Cloud Run](https://docs.cloud.google.com/run/docs/quickstarts/build-and-deploy/deploy-python-streamlit-service)
- [Deploy services from source code](https://docs.cloud.google.com/run/docs/deploying-source-code)
- [Allow public access to a Cloud Run service](https://docs.cloud.google.com/run/docs/authenticating/public)
