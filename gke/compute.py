import pulumi_gcp as gcp

class GkeNodePoolStack:
    def __init__(
        self, 
        name: str, 
        region: str,
        cluster_name: str,
        preemtible: bool = True,
        machine_type: str = "n1-standard-1"
    ):
    
        self.node_pool = gcp.container.NodePool(
            resource_name=f"{name}-node-pool",
            location=region,
            cluster=cluster_name,
            initial_node_count=1,
            autoscaling=gcp.container.ClusterNodePoolAutoscalingArgs(
                min_node_count=1,
                max_node_count=1,
            ),
            node_config=gcp.container.ClusterNodeConfigArgs(
                machine_type=machine_type,
                preemptible= preemtible,
                oauth_scopes=[
                    "https://www.googleapis.com/auth/cloud-platform",
                    'https://www.googleapis.com/auth/compute',
                    'https://www.googleapis.com/auth/devstorage.read_only',
                    'https://www.googleapis.com/auth/logging.write',
                    'https://www.googleapis.com/auth/monitoring'
                ],
            ),
        )