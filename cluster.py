import pulumi
from pulumi_gcp import container

class GkeClusterStack:
    def __init__(
            self, 
            name: str, 
            region: str, 
            zone: str, 
            vpc_id: str, 
            public_subnet_id: str, 
            private_subnet_id: str,
            gke_version: str
        ):
        # Create the GKE cluster using the provided VPC and subnets
        self.gke_cluster = container.Cluster(
            f"{name}-cluster",
            name=name,
            initial_node_count=1,  # One compute node
            location=zone,
            min_master_version=gke_version,
            network=vpc_id,
            subnetwork=private_subnet_id,  # Use the private subnet for cluster nodes
            node_config=container.ClusterNodeConfigArgs(
                machine_type="n1-standard-1",  # One standard compute node
                oauth_scopes=[
                    "https://www.googleapis.com/auth/cloud-platform"
                ],
            ),
        )

        # Export cluster name and endpoint
        pulumi.export("clusterName", self.gke_cluster.name)
        pulumi.export("clusterEndpoint", self.gke_cluster.endpoint)
