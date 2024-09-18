import pulumi
from pulumi_gcp import container

class GkeClusterStack:
    def __init__(
        self, 
        name: str, 
        region: str, 
        vpc_id: str, 
        private_subnet_id: str,
        gke_version: str
    ):

        self.gke_cluster = container.Cluster(
            f"{name}-cluster",
            name=name,
            location=region,
            min_master_version=gke_version,
            network=vpc_id,
            subnetwork=private_subnet_id,
            remove_default_node_pool=True,
            initial_node_count=1
        )

        pulumi.export("clusterName", self.gke_cluster.name)
        pulumi.export("clusterEndpoint", self.gke_cluster.endpoint)