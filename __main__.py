import pulumi
from network import NetworkStack
from cluster import GkeClusterStack
from pulumi_gcp import container

# Load configuration
config = pulumi.Config()

# Define variables
cluster_name = config.require("cluster_name")
region = "europe-west1"
zone = "europe-west1"
latest_engine_version = container.get_engine_versions(location=region).release_channel_latest_version['REGULAR']
pulumi.export("latest_engine_version", latest_engine_version)

network_stack = NetworkStack(
    name=cluster_name,
    config=config,
    region=region
)

gke_cluster_stack = GkeClusterStack(
    name=cluster_name,
    region=region,
    zone=zone,
    vpc_id=network_stack.vpc.id,
    public_subnet_id=network_stack.public_subnet.id,
    private_subnet_id=network_stack.private_subnet.id,
    gke_version=latest_engine_version
)