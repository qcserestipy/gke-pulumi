# GKE Pulumi Project

This repository is a Pulumi-based infrastructure-as-code (IaC) project for deploying a Google Kubernetes Engine (GKE) cluster on Google Cloud, along with a configurable node pool and networking resources. The project is written in Python and uses the Pulumi GCP SDK.

## Project Structure

- **`__main__.py`**: The main entry point for Pulumi, which orchestrates the creation of the network, GKE cluster, and node pool.
- **`network.py`**: Defines the `NetworkStack` class that provisions a Virtual Private Cloud (VPC) and subnets for the GKE cluster.
- **`cluster.py`**: Contains the `GkeClusterStack` class responsible for creating the GKE cluster using the provided VPC and subnets.
- **`compute.py`**: Defines the `GkeNodePoolStack` class that provisions a GKE node pool attached to the cluster.

## Requirements

- **Pulumi**: The Pulumi CLI must be installed. You can install it by following the [Pulumi installation guide](https://www.pulumi.com/docs/get-started/install/).
- **Google Cloud SDK**: Ensure the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) is installed and authenticated.
- **Python**: This project uses Python, so you will need `python3` and `pip` installed.
  
## Setup

1. **Install Pulumi**:
   Follow the installation guide at [Pulumi Installation](https://www.pulumi.com/docs/get-started/install/).

2. **Install Python dependencies**:
   Install the required Python packages by running:
   ```bash
   pip install -r requirements.txt

# Notes: Commands needed for github actions service account

```
export PROJECT_ID=yukaringermany-gke 

gcloud services enable iap.googleapis.com

gcloud iam workload-identity-pools create "githuboauthpool" \
    --project="${PROJECT_ID}" \
    --location="global" 
          
gcloud iam workload-identity-pools providers create-oidc "githuboauth-provider" \
    --project="${PROJECT_ID}" \
    --location="global" \
    --workload-identity-pool="githuboauthpool" \
    --display-name="githuboauth-provider" \
    --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.actor=assertion.actor,attribute.aud=assertion.aud" \
    --issuer-uri="https://token.actions.githubusercontent.com" \
    --attribute-condition="assertion.repository == 'qcserestipy/gke-pulumi'"  

gcloud iam service-accounts create githubactions \
    --project="${PROJECT_ID}" \
    --display-name="Service account for GitHub Actions"   

gcloud iam service-accounts add-iam-policy-binding "githubactions@${PROJECT_ID}.iam.gserviceaccount.com" \
    --project="${PROJECT_ID}" \
    --role="roles/iam.workloadIdentityUser" \
    --member="principalSet://iam.googleapis.com/projects/619157711315/locations/global/workloadIdentityPools/githuboauthpool/attribute.repository/qcserestipy/gke-pulumi"

gcloud services enable container.googleapis.com --project=${PROJECT_ID}

gcloud projects add-iam-policy-binding ${PROJECT_ID} \ 
    --member="serviceAccount:githubactions@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/container.admin"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
   --member="serviceAccount:githubactions@${PROJECT_ID}.iam.gserviceaccount.com" \
   --role="roles/compute.networkAdmin"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
   --member="serviceAccount:githubactions@${PROJECT_ID}.iam.gserviceaccount.com" \
   --role="roles/container.admin"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:githubactions@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:githubactions@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser" \
    --condition=None

gcloud services enable cloudresourcemanager.googleapis.com --project yukaringermany-gke

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
   --member="serviceAccount:githubactions@${PROJECT_ID}.iam.gserviceaccount.com" \
   --role="roles/iam.serviceAccountAdmin"

gcloud container clusters get-credentials yukaringermany-gke --region us-central1 --project yukaringermany-gke

```