import pulumi
from pulumi_gcp import container
from gke.network import NetworkStack
from gke.cluster import GkeClusterStack 
from gke.compute import GkeNodePoolStack
from gke.bastion import GkeBastionHostStack
from gke.moodle import MoodleStack

# Load configuration
config = pulumi.Config()

# Define variables
cluster_name = config.require("cluster_name")
region = config.require("cluster_region")
zone = config.require("cluster_region")
latest_engine_version = container.get_engine_versions(location=region).release_channel_latest_version['REGULAR']
pulumi.export("latest_engine_version", latest_engine_version)

network_stack = NetworkStack(
    name=cluster_name,
    region=region
)

gke_cluster_stack = GkeClusterStack(
    name=cluster_name,
    region=region,
    vpc_id=network_stack.vpc.id,
    private_subnet=network_stack.private_subnet,
    gke_version=latest_engine_version
)

gke_nodepool_stack = GkeNodePoolStack(
    name=cluster_name,
    region=region,
    cluster_name=gke_cluster_stack.gke_cluster.name,
    machine_type='e2-small'
)

gke_bastion_host = GkeBastionHostStack(
    vpc_id=network_stack.vpc.id,
    region=region,
    private_subnet_id=network_stack.private_subnet.id,
)


from pulumi_kubernetes.apps.v1 import Deployment

deployment = Deployment(
    "nginx-deployment",
    spec={
        "selector": {"matchLabels": {"app": "nginx"}},
        "replicas": 2,
        "template": {
            "metadata": {"labels": {"app": "nginx"}},
            "spec": {
                "containers": [
                    {
                        "name": "nginx",
                        "image": "nginx",
                        "ports": [{"containerPort": 80}],
                    }
                ]
            },
        },
    },
    opts=pulumi.ResourceOptions(provider=gke_cluster_stack.k8s_provider)
)


moodle_stack = MoodleStack(
    name="moodle",
    region=region,
    vpc=network_stack.vpc,
    k8s_provider=gke_cluster_stack.k8s_provider,
    cluster_name=gke_cluster_stack.gke_cluster.name
)