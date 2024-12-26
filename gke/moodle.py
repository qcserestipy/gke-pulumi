import pulumi
import pulumi_gcp as gcp
import pulumi_kubernetes as k8s
from pulumi import ResourceOptions

class MoodleStack:
    def __init__(
        self,
        name: str,
        region: str,
        vpc,
        vpc_peering,
        k8s_provider: k8s.Provider,
        cluster_name: pulumi.Output[str],
    ):

        # ---------------------------------------------------------------------------------------
        # 1) Cloud Filestore (NFS) for moodledata
        # ---------------------------------------------------------------------------------------
        # Reserve a small /29 block for Filestore inside your VPC. 
        # Adjust `reserved_ip_range` capacity as you need.
        self.moodle_filestore = gcp.filestore.Instance(
            f"{name}-filestore",
            tier="BASIC_HDD",
            location=f"{region}-a",
            file_shares={
                "name": "moodle",
                "capacityGb": 1024,
            },
            networks=[
                gcp.filestore.InstanceNetworkArgs(
                    network=vpc.id,
                    modes=["MODE_IPV4"],
                    reserved_ip_range="10.2.0.0/29",
                )
            ],
        )

        # ---------------------------------------------------------------------------------------
        # 2) Cloud Memorystore (Redis) for caching
        # ---------------------------------------------------------------------------------------
        # Standard tier for high-availability. Adjust memory size, region, version, and networking
        self.moodle_redis = gcp.redis.Instance(
            f"{name}-redis",
            tier="STANDARD_HA",
            memory_size_gb=1,
            region=region,
            redis_version="REDIS_7_2",
            transit_encryption_mode="SERVER_AUTHENTICATION",  # Optional, for TLS
            authorized_network=vpc.id,
        )

        # ---------------------------------------------------------------------------------------
        # 3) Cloud SQL (MySQL) for Moodle’s DB
        # ---------------------------------------------------------------------------------------
        self.moodle_db_instance = gcp.sql.DatabaseInstance(
            f"{name}-db-instance",
            database_version="MYSQL_8_0",
            region=region,
            settings={
                "tier": "db-n1-standard-1",
                "ip_configuration": {
                    "ipv4_enabled": False,
                    "private_network": vpc.self_link,
                },
            },
            opts=pulumi.ResourceOptions(depends_on=[vpc_peering])
        )
        # Create the actual database
        self.moodle_db = gcp.sql.Database(
            f"{name}-db",
            instance=self.moodle_db_instance.name,
            name="moodledb",
        )
        # Create a DB user
        self.moodle_db_user = gcp.sql.User(
            f"{name}-db-user",
            instance=self.moodle_db_instance.name,
            name=pulumi.Config().require_secret("dbUser"),
            password=pulumi.Config().require_secret("dbPassword"),
        )

        # ---------------------------------------------------------------------------------------
        # 4) Deploy Moodle on GKE
        # ---------------------------------------------------------------------------------------
        # Create a dedicated namespace in your cluster
        self.moodle_ns = k8s.core.v1.Namespace(
            f"{name}-namespace",
            metadata={
                "name": "moodle"
            },
            opts=ResourceOptions(provider=k8s_provider),
        )

        # We’ll need the IP/hostname of Filestore & Redis
        filestore_ip = self.moodle_filestore.networks[0].ip_addresses[0]
        redis_host = self.moodle_redis.host
        redis_port = self.moodle_redis.port.apply(lambda p: str(p))

        # We also need Cloud SQL connection name
        db_conn_name = self.moodle_db_instance.connection_name

        # Define Moodle Deployment
        # In production, you’d store these in secrets and config maps. 
        # Adjust the container image and env vars as needed.
        self.moodle_deployment = k8s.apps.v1.Deployment(
            f"{name}-deployment",
            metadata={
                "name": "moodle-deployment",
                "namespace": self.moodle_ns.metadata["name"],
                "labels": {"app": "moodle"},
            },
            spec={
                "replicas": 2,
                "selector": {
                    "matchLabels": {"app": "moodle"}
                },
                "template": {
                    "metadata": {
                        "labels": {"app": "moodle"},
                    },
                    "spec": {
                        "containers": [
                            {
                                "name": "moodle",
                                "image": "bitnami/moodle:latest",  # or another Moodle container
                                "ports": [{"containerPort": 80, "name": "http"}],
                                "env": [
                                    {
                                        "name": "MOODLE_DATABASE_HOST",
                                        "value": db_conn_name,
                                    },
                                    {
                                        "name": "MOODLE_DATABASE_NAME",
                                        "value": self.moodle_db.name,
                                    },
                                    {
                                        "name": "MOODLE_DATABASE_USER",
                                        "value": self.moodle_db_user.name,
                                    },
                                    {
                                        "name": "MOODLE_DATABASE_PASSWORD",
                                        "value": "S3cureP@ss!",
                                    },
                                    {
                                        "name": "MOODLE_REDIS_HOST",
                                        "value": redis_host,
                                    },
                                    {
                                        "name": "MOODLE_REDIS_PORT",
                                        "value": redis_port,
                                    },
                                    # Example additional config
                                    # {"name": "MOODLE_REDIS_PASSWORD", "value": "..."},
                                ],
                                "volumeMounts": [
                                    {
                                        "name": "moodle-data",
                                        "mountPath": "/bitnami/moodle",
                                    }
                                ],
                            }
                        ],
                        "volumes": [
                            {
                                "name": "moodle-data",
                                "nfs": {
                                    "server": filestore_ip,
                                    "path": "/moodle",  # matches the FileShare name
                                },
                            }
                        ],
                    },
                },
            },
            opts=ResourceOptions(provider=k8s_provider),
        )

        # Expose Moodle via a Kubernetes Service (NodePort or ClusterIP)
        self.moodle_service = k8s.core.v1.Service(
            f"{name}-service",
            metadata={
                "name": "moodle-service",
                "namespace": self.moodle_ns.metadata["name"],
                "labels": {"app": "moodle"},
            },
            spec={
                "type": "NodePort",
                "selector": {"app": "moodle"},
                "ports": [
                    {
                        "name": "http",
                        "port": 80,
                        "targetPort": "http",
                    }
                ],
            },
            opts=ResourceOptions(provider=k8s_provider),
        )

        # ---------------------------------------------------------------------------------------
        # 5) Cloud Armor + Cloud CDN via GKE Ingress
        # ---------------------------------------------------------------------------------------
        # (a) Create a Cloud Armor Security Policy
        self.cloud_armor_policy = gcp.compute.SecurityPolicy(
            f"{name}-armor-policy",
            description="Basic Cloud Armor policy for Moodle",
            rules=[
                # Example rule blocking all traffic from a malicious IP
                # gcp.compute.SecurityPolicyRuleArgs(...)
            ],
        )

        # (b) Create a BackendConfig for GCE Ingress that references
        #     Cloud Armor policy and enables Cloud CDN
        # Note: The “cloud.google.com/v1beta1” CRD must be installed 
        #       in the cluster (it typically is, by default).
        self.backend_config = k8s.apiextensions.CustomResource(
            f"{name}-backendconfig",
            api_version="cloud.google.com/v1beta1",
            kind="BackendConfig",
            metadata={
                "name": "moodle-backendconfig",
                "namespace": self.moodle_ns.metadata["name"],
            },
            spec={
                "securityPolicy": {
                    "name": self.cloud_armor_policy.name,
                },
                "cdn": {
                    "enabled": True,
                },
            },
            opts=ResourceOptions(provider=k8s_provider),
        )

        # (c) Create the Ingress with relevant annotations
        self.moodle_ingress = k8s.networking.v1.Ingress(
            f"{name}-ingress",
            metadata={
                "name": "moodle-ingress",
                "namespace": self.moodle_ns.metadata["name"],
                "annotations": {
                    "kubernetes.io/ingress.class": "gce",
                    # Attach to the custom BackendConfig we created
                    "cloud.google.com/backend-config": '{"default":"moodle-backendconfig"}',
                    # For example if you have a Global Static IP
                    # "kubernetes.io/ingress.global-static-ip-name": "moodle-static-ip",
                    # If you have an existing managed SSL cert
                    # "ingress.gcp.kubernetes.io/pre-shared-cert": "moodle-ssl-cert",
                },
            },
            spec={
                "rules": [
                    {
                        "http": {
                            "paths": [
                                {
                                    "path": "/*",
                                    "pathType": "ImplementationSpecific",
                                    "backend": {
                                        "service": {
                                            "name": self.moodle_service.metadata["name"],
                                            "port": {
                                                "number": 80
                                            },
                                        }
                                    },
                                }
                            ]
                        }
                    }
                ]
            },
            opts=ResourceOptions(provider=k8s_provider),
        )

        # ---------------------------------------------------------------------------------------
        # 6) reCAPTCHA Enterprise (not directly supported as a Pulumi resource yet)
        # ---------------------------------------------------------------------------------------
        # You would typically:
        #   1. Enable the reCAPTCHA Enterprise API in your project.
        #   2. Create a site key from the console or with the REST API/gcloud.
        #   3. Configure your Moodle instance (in the Moodle admin panel or config) 
        #      to use that site key for login forms, etc.
        #
        # For referencing the site key in Pulumi, you might store it in config/secrets 
        # or retrieve it at runtime. But there is no direct pulumi_gcp.* resource 
        # for reCAPTCHA Enterprise at the time of writing.

        # ---------------------------------------------------------------------------------------
        # 7) Output some helpful connection info
        # ---------------------------------------------------------------------------------------
        pulumi.export("filestoreIP", filestore_ip)
        pulumi.export("redisHost", redis_host)
        pulumi.export("redisPort", redis_port)
        pulumi.export("dbConnectionName", db_conn_name)
        pulumi.export("moodleURL", self.moodle_ingress.status.apply(
            lambda s: f"http://{s.load_balancer.ingress[0].ip}" 
            if s and s.load_balancer and s.load_balancer.ingress 
            else "Provisioning..."
        ))
