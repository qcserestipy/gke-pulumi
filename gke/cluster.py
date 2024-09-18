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
            deletion_protection=False,
            initial_node_count=1,
            private_cluster_config=container.ClusterPrivateClusterConfigArgs(
                enable_private_nodes=True,
                enable_private_endpoint=False,
                master_ipv4_cidr_block="10.0.0.0/28"
            ),
            # master_authorized_networks_config=container.ClusterMasterAuthorizedNetworksConfigArgs(
            #     cidr_blocks=[
            #         container.ClusterMasterAuthorizedNetworksConfigCidrBlockArgs(
            #             cidr_block="93.203.225.76/32",  # Change this to restrict access, such as to a trusted IP range
            #             display_name="Allow Me", 
                        
            #         )
            #     ],
            # ),
        )

        pulumi.export("clusterName", self.gke_cluster.name)
        pulumi.export("clusterEndpoint", self.gke_cluster.endpoint)
