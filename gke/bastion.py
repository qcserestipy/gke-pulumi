import pulumi_gcp as gcp

class GkeBastionHostStack:
    def __init__(
        self,
        region: str,
        vpc_id: str,
        public_subnet_id: str,
        name: str = "gke-bastion-host", 
        machine_type: str = "e2-micro",
        image: str = "debian-cloud/debian-11",
    ):

        # Create a service account for the bastion host
        self.service_account = gcp.serviceaccount.Account(
            f"{name}-sa",
            account_id=f"{name}-sa",
            display_name="GKE Bastion Host Service Account",
        )

        # Grant roles to the service account
        self.viewer_role_binding = gcp.projects.IAMMember(
            f"{name}-viewer-role-binding",
            project=gcp.config.project,
            role="roles/container.clusterViewer",  # Allows viewing cluster details
            member=self.service_account.email.apply(lambda email: f"serviceAccount:{email}"),
        )

        self.admin_role_binding = gcp.projects.IAMMember(
            f"{name}-admin-role-binding",
            project=gcp.config.project,
            role="roles/container.admin",  # Allows administrative access to the cluster
            member=self.service_account.email.apply(lambda email: f"serviceAccount:{email}"),
        )        

        # Create the bastion host and associate the service account
        self.bastion_host = gcp.compute.Instance(
            name,
            zone=region,
            machine_type=machine_type,
            boot_disk=gcp.compute.InstanceBootDiskArgs(
                initialize_params=gcp.compute.InstanceBootDiskInitializeParamsArgs(
                    image=image,
                ),
            ),
            network_interfaces=[
                gcp.compute.InstanceNetworkInterfaceArgs(
                    network=vpc_id,
                    subnetwork=public_subnet_id,
                    access_configs=[gcp.compute.InstanceNetworkInterfaceAccessConfigArgs()],
                )
            ],
            service_account=gcp.compute.InstanceServiceAccountArgs(
                email=self.service_account.email,
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            ),
            metadata_startup_script="""
                #!/bin/bash
                sudo apt-get update && sudo apt-get install -y google-cloud-sdk
            """
        )