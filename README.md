# Commands needed for github actions service account

```
export PROJECT_ID=yukaringermany-gke 

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

```