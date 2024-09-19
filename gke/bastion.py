import pulumi_gcp as gcp

class GkeBastionHostStack:
    def __init__(
        self,
        region: str,
        vpc_id: str,
        private_subnet_id: str,
        name: str = "gke-bastion-host", 
        machine_type: str = "e2-micro",
        image: str = "debian-cloud/debian-11",
    ):

        # This bastion host is implemented according to:
        # https://cloud.google.com/kubernetes-engine/docs/tutorials/private-cluster-bastion 
        
        # Define network tag to identify the bastion host
        bastion_host_tag = f"{name}-tag"

        # Create a service account for the bastion host
        self.service_account = gcp.serviceaccount.Account(
            f"{name}-sa",
            account_id=f"{name}-sa",
            display_name="GKE Bastion Host Service Account",
        )

        # # Grant roles to the service account
        # self.viewer_role_binding = gcp.projects.IAMMember(
        #     f"{name}-viewer-role-binding",
        #     project=gcp.config.project,
        #     role="roles/container.clusterViewer",  # Allows viewing cluster details
        #     member=self.service_account.email.apply(lambda email: f"serviceAccount:{email}"),
        # )

        # self.admin_role_binding = gcp.projects.IAMMember(
        #     f"{name}-admin-role-binding",
        #     project=gcp.config.project,
        #     role="roles/container.admin",  # Allows administrative access to the cluster
        #     member=self.service_account.email.apply(lambda email: f"serviceAccount:{email}"),
        # )        

        # Create the bastion host and associate the service account
        self.bastion_host = gcp.compute.Instance(
            name,
            zone=f"{region}-a",
            machine_type=machine_type,
            boot_disk=gcp.compute.InstanceBootDiskArgs(
                initialize_params=gcp.compute.InstanceBootDiskInitializeParamsArgs(
                    image=image,
                ),
            ),
            # network_interfaces=[
            #     gcp.compute.InstanceNetworkInterfaceArgs(
            #         network=vpc_id,
            #         subnetwork=public_subnet_id,
            #         access_configs=[gcp.compute.InstanceNetworkInterfaceAccessConfigArgs()],
            #     )
            # ],
            network_interfaces=[
                gcp.compute.InstanceNetworkInterfaceArgs(
                    network=vpc_id,
                    subnetwork=private_subnet_id,
                    access_configs=[],  # No external IP (no access config)
                )
            ],
            service_account=gcp.compute.InstanceServiceAccountArgs(
                email=self.service_account.email,
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            ),
            metadata_startup_script="""
                #!/bin/bash
                # Install necessary packages including Tinyproxy
                sudo apt-get update
                sudo apt-get install -y google-cloud-sdk tinyproxy

                # Configure Tinyproxy
                sudo sed -i 's/^Port .*/Port 8888/' /etc/tinyproxy/tinyproxy.conf  # Ensure port 8888
                sudo sed -i '/^#Allow 127.0.0.1/a Allow localhost' /etc/tinyproxy/tinyproxy.conf  # Add Allow localhost

                # Restart Tinyproxy service
                sudo service tinyproxy restart
            """,
            tags=[bastion_host_tag],
        )

        # Create firewall rule to allow ingress from IAP IP range
        self.iap_firewall_rule = gcp.compute.Firewall(
            f"{name}-allow-ingress-from-iap",
            network=vpc_id,
            allows=[
                gcp.compute.FirewallAllowArgs(
                    protocol="tcp",
                    ports=["22"],  # Allow SSH
                ),
            ],
            direction="INGRESS",
            source_ranges=["35.235.240.0/20"],  # IAP IP range
            target_tags=[bastion_host_tag],  # Optional: apply to specific instances
            description="Allow ingress from IAP for SSH access"
        )

        # Create firewall rule to allow egress (outbound) traffic to the internet
        self.egress_firewall_rule = gcp.compute.Firewall(
            f"{name}-allow-egress",
            network=vpc_id,
            allows=[
                gcp.compute.FirewallAllowArgs(
                    protocol="tcp",  # You can also specify "all" if you want to allow all protocols
                    ports=["0-65535"],  # Allow all TCP ports
                ),
                gcp.compute.FirewallAllowArgs(
                    protocol="udp",  # Allow all UDP ports
                    ports=["0-65535"],
                ),
                gcp.compute.FirewallAllowArgs(
                    protocol="icmp",  # Allow ICMP traffic (optional, useful for ping)
                ),
            ],
            direction="EGRESS",
            destination_ranges=["0.0.0.0/0"],  # Allow all outbound traffic
            target_tags=[bastion_host_tag],  # Apply to bastion host instances
            description="Allow egress traffic to the internet for bastion host"
        )