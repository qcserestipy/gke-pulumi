import pulumi
from pulumi_gcp import compute

class NetworkStack:
    def __init__(self, name: str, region: str):
        # Create a VPC Network
        self.vpc = compute.Network(
            f"{name}-vpc",
            auto_create_subnetworks=False,
        )

        # Create a Cloud Router for managing NAT traffic
        self.router = compute.Router(
            f"{name}-router",
            network=self.vpc.id,
            region=region,
        )

        # Create public and private subnets
        self.public_subnet = compute.Subnetwork(
            f"{name}-public-subnet",
            ip_cidr_range="10.0.64.0/19",
            region=region,
            network=self.vpc.id,
            description="Public Subnet for GKE",
        )

        self.private_subnet = compute.Subnetwork(
            f"{name}-private-subnet",
            ip_cidr_range="10.0.32.0/19",
            region=region,
            network=self.vpc.id,
            description="Private Subnet for GKE",
            purpose="PRIVATE",
            private_ip_google_access=True,  # Enable Private Google Access for GCP API access
        )

        self.nat_gateway = compute.RouterNat(
            f"{name}-nat-gateway",
            router=self.router.name,
            region=region,
            nat_ip_allocate_option="AUTO_ONLY",
            source_subnetwork_ip_ranges_to_nat="ALL_SUBNETWORKS_ALL_IP_RANGES",  # NAT for all subnets
            log_config=compute.RouterNatLogConfigArgs(
                enable=True,
                filter="ERRORS_ONLY",
            ),
        )

        self.egress_firewall_rule = compute.Firewall(
            f"{name}-allow-egress",
            network=self.vpc.id,
            allows=[
                compute.FirewallAllowArgs(
                    protocol="all", 
                ),
            ],
            direction="EGRESS",
            description="Allow all egress traffic",
            priority=1000,
        )

        self.internal_firewall_rule = compute.Firewall(
            f"{name}-allow-internal",
            network=self.vpc.id,
            allows=[
                compute.FirewallAllowArgs(
                    protocol="tcp",
                    ports=["0-65535"],
                ),
                compute.FirewallAllowArgs(
                    protocol="udp",
                    ports=["0-65535"],
                ),
                compute.FirewallAllowArgs(
                    protocol="icmp",
                ),
            ],
            direction="INGRESS",
            source_ranges=["10.0.0.0/8"],
            description="Allow internal communication between nodes",
        )

        # Export the VPC and subnet IDs for use in other stacks
        pulumi.export("vpcId", self.vpc.id)
        pulumi.export("publicSubnetId", self.public_subnet.id)
        pulumi.export("privateSubnetId", self.private_subnet.id)
