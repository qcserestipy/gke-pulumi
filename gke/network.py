import pulumi
from pulumi_gcp import compute

class NetworkStack:
    def __init__(self, name: str, config: pulumi.Config, region: str):
        # Create a VPC Network
        self.vpc = compute.Network(
            f"{name}-vpc",
            auto_create_subnetworks=False,
        )

        # Create public and private subnets without the 'tags' argument
        self.public_subnet = compute.Subnetwork(
            f"{name}-public-subnet",
            ip_cidr_range="10.0.64.0/19",
            region=region,
            network=self.vpc.id,
            description="Public Subnet for GKE",
            # purpose="PRIVATE_RFC_1918"
        )

        self.private_subnet = compute.Subnetwork(
            f"{name}-private-subnet",
            ip_cidr_range="10.0.32.0/19",
            region=region,
            network=self.vpc.id,
            description="Private Subnet for GKE",
            # purpose="PRIVATE_NAT",
            private_ip_google_access=True,
        )

        # Export the VPC and subnet IDs
        pulumi.export("vpcId", self.vpc.id)
        pulumi.export("publicSubnetId", self.public_subnet.id)
        pulumi.export("privateSubnetId", self.private_subnet.id)
