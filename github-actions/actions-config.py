import pulumi
import pulumi_gcp as gcp

# Define variables
project_id = "spry-catcher-449515-h2"
workload_pool_name = "githuboauth-pool"
provider_name = "githuboauth-provider"
service_account_name = "githubactions"
repo_name = "qcserestipy/gke-pulumi"

# Enable the necessary GCP services
iap_service = gcp.projects.Service("iap-service",
    service="iap.googleapis.com"
)

container_service = gcp.projects.Service("container-service",
    service="container.googleapis.com"
)

cloudresourcemanager_service = gcp.projects.Service("cloudresourcemanager-service",
    service="cloudresourcemanager.googleapis.com"
)

# Create Workload Identity Pool
workload_pool = gcp.iam.WorkloadIdentityPool(workload_pool_name,
    location="global",
    project=project_id
)

# Create OIDC provider within the pool
oidc_provider = gcp.iam.WorkloadIdentityPoolProvider(provider_name,
    workload_identity_pool_id=workload_pool.workload_identity_pool_id,
    display_name=provider_name,
    oidc=gcp.iam.WorkloadIdentityPoolProviderOidcArgs(
        issuer_uri="https://token.actions.githubusercontent.com"
    ),
    attribute_mappings={
        "google.subject": "assertion.sub",
        "attribute.repository": "assertion.repository",
        "attribute.actor": "assertion.actor",
        "attribute.aud": "assertion.aud"
    },
    attribute_condition=f"assertion.repository == '{repo_name}'",
    location="global",
    project=project_id
)

# Create a service account for GitHub Actions
service_account = gcp.serviceaccount.Account(service_account_name,
    account_id=service_account_name,
    display_name="Service account for GitHub Actions",
    project=project_id
)

# Bind roles to the service account
roles = [
    "roles/container.admin",
    "roles/compute.networkAdmin",
    "roles/storage.admin",
    "roles/iam.serviceAccountUser",
    "roles/iam.serviceAccountAdmin",
    "roles/resourcemanager.projectIamAdmin",
    "roles/compute.instanceAdmin.v1",
    "roles/compute.storageAdmin"
]

# Assign IAM roles to the service account
for role in roles:
    gcp.projects.IAMMember(f"{service_account_name}-{role}",
        project=project_id,
        role=role,
        member=f"serviceAccount:{service_account.email}"
    )

# Bind Workload Identity Federation to the service account
gcp.projects.IAMMember("workload-identity-binding",
    project=project_id,
    role="roles/iam.workloadIdentityUser",
    member=f"principalSet://iam.googleapis.com/projects/{project_id}/locations/global/workloadIdentityPools/{workload_pool_name}/attribute.repository/{repo_name}"
)

pulumi.export("workload_pool_id", workload_pool.id)
pulumi.export("oidc_provider", oidc_provider.id)
pulumi.export("service_account_email", service_account.email)
