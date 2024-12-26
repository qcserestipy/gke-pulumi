import pulumi
from pulumi_gcp import container, compute, config as gcp_config
import pulumi_kubernetes as k8s

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
                enable_private_endpoint=False,
                master_ipv4_cidr_block="10.0.0.0/28"
            ),
            master_authorized_networks_config=container.ClusterMasterAuthorizedNetworksConfigArgs(
                cidr_blocks=[
                    container.ClusterMasterAuthorizedNetworksConfigCidrBlockArgs(
                        cidr_block="0.0.0.0/0",
                        #private_subnet.ip_cidr_range,
                        display_name="Allow VPC Traffic", 
                    )
                ],
            ),
            # Request sensitive info
            master_auth=container.ClusterMasterAuthArgs(
                client_certificate_config=container.ClusterMasterAuthClientCertificateConfigArgs(
                    issue_client_certificate=True  # Ensure sensitive fields are returned
                )
            ),
        )

        # # Create the Kubernetes provider using the kubeconfig
        # self.k8s_provider = k8s.Provider(f"{name}-provider", kubeconfig=self.generate_kubeconfig())

        pulumi.export("clusterName", self.gke_cluster.name)
        pulumi.export("clusterEndpoint", self.gke_cluster.endpoint)
        pulumi.export("debugMasterAuth", self.gke_cluster.master_auth)

#     def generate_kubeconfig(self):
#         """Create kubeconfig to access the cluster."""
#         return pulumi.Output.all(self.gke_cluster.name, self.gke_cluster.endpoint, self.gke_cluster.master_auth).apply(
#             lambda args: self.create_kubeconfig(*args)
#         )

#     def create_kubeconfig(self, name, endpoint, master_auth):
#         """Generate kubeconfig string for the cluster."""
#         ca_cert = master_auth.get('clusterCaCertificate', None)
#         # ca_cert = master_auth.get('client_certificate', None)
#         if not ca_cert:
#             raise ValueError(f"Failed to retrieve cluster CA certificate from master_auth. Content of master_auth: {master_auth}")
#         context = f"{gcp_config.project}_{gcp_config.zone}_{name}"
#         return f"""
# apiVersion: v1
# clusters:
# - cluster:
#     certificate-authority-data: {ca_cert}
#     server: https://{endpoint}
#   name: {context}
# contexts:
# - context:
#     cluster: {context}
#     user: {context}
#   name: {context}
# current-context: {context}
# kind: Config
# preferences: {{}}
# users:
# - name: {context}
#   user:
#     exec:
#       apiVersion: client.authentication.k8s.io/v1beta1
#       command: gke-gcloud-auth-plugin
#       installHint: Install gke-gcloud-auth-plugin for use with kubectl by following
#         https://cloud.google.com/blog/products/containers-kubernetes/kubectl-auth-changes-in-gke
#       provideClusterInfo: true
# """