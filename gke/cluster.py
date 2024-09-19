import pulumi
from pulumi_gcp import container, compute

class GkeClusterStack:
    def __init__(
        self, 
        name: str, 
        region: str, 
        vpc_id: str, 
        private_subnet: compute.Subnetwork,
        gke_version: str
    ):

        self.gke_cluster = container.Cluster(
            f"{name}-cluster",
            name=name,
            location=region,
            min_master_version=gke_version,
            network=vpc_id,
            subnetwork=private_subnet.id,
            remove_default_node_pool=True,
            deletion_protection=False,
            initial_node_count=1,
            private_cluster_config=container.ClusterPrivateClusterConfigArgs(
                enable_private_nodes=True,
                enable_private_endpoint=True,
                master_ipv4_cidr_block="10.0.0.0/28"
            ),
            master_authorized_networks_config=container.ClusterMasterAuthorizedNetworksConfigArgs(
                cidr_blocks=[
                    container.ClusterMasterAuthorizedNetworksConfigCidrBlockArgs(
                        cidr_block=private_subnet.ip_cidr_range,
                        display_name="Allow VPC Traffic", 
                    )
                ],
            ),
        )

        pulumi.export("clusterName", self.gke_cluster.name)
        pulumi.export("clusterEndpoint", self.gke_cluster.endpoint)
