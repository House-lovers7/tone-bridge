# インフラストラクチャアーキテクチャ仕様書

## 1. 概要

ToneBridgeのインフラストラクチャは、クラウドネイティブアーキテクチャを採用し、高可用性、スケーラビリティ、セキュリティを実現します。本仕様書では、インフラストラクチャの設計、構成、運用について詳細に説明します。

## 2. インフラストラクチャ全体構成

### 2.1 マルチクラウド対応アーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│                     Global Traffic Manager                    │
│                    (Route53 / CloudFlare)                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│   AWS Region  │  │   GCP Region  │  │  Azure Region │
│  (Primary)    │  │  (Secondary)  │  │   (Backup)    │
└───────────────┘  └───────────────┘  └───────────────┘
        │                  │                  │
        ▼                  ▼                  ▼
   Kubernetes         Kubernetes         Kubernetes
     Cluster           Cluster            Cluster
```

### 2.2 ネットワークアーキテクチャ

```
Internet
    │
    ├─ CloudFlare (CDN/WAF)
    │   ├─ DDoS Protection
    │   ├─ Rate Limiting
    │   └─ Geographic Routing
    │
    ├─ Load Balancer (Layer 7)
    │   ├─ SSL Termination
    │   ├─ Path-based Routing
    │   └─ Health Checks
    │
    ├─ VPC (10.0.0.0/16)
    │   ├─ Public Subnet (10.0.1.0/24)
    │   │   ├─ NAT Gateway
    │   │   └─ Bastion Host
    │   │
    │   ├─ Private Subnet - App (10.0.10.0/24)
    │   │   ├─ Kubernetes Nodes
    │   │   └─ Application Pods
    │   │
    │   ├─ Private Subnet - Data (10.0.20.0/24)
    │   │   ├─ PostgreSQL
    │   │   ├─ Redis
    │   │   └─ Elasticsearch
    │   │
    │   └─ Private Subnet - Management (10.0.30.0/24)
    │       ├─ Monitoring Stack
    │       └─ CI/CD Tools
```

## 3. Kubernetes アーキテクチャ

### 3.1 クラスター構成

```yaml
# EKS/GKE/AKS Configuration
cluster:
  name: tonebridge-production
  version: "1.28"
  region: us-west-2
  
  node_pools:
    - name: system
      instance_type: t3.medium
      min_size: 2
      max_size: 5
      labels:
        workload: system
      taints:
        - key: CriticalAddonsOnly
          value: "true"
          effect: NoSchedule
    
    - name: application
      instance_type: c5.xlarge
      min_size: 3
      max_size: 20
      labels:
        workload: application
      
    - name: database
      instance_type: r5.2xlarge
      min_size: 3
      max_size: 6
      labels:
        workload: database
      taints:
        - key: database
          value: "true"
          effect: NoSchedule
```

### 3.2 Namespace構成

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    environment: production
    
---
apiVersion: v1
kind: Namespace
metadata:
  name: staging
  labels:
    environment: staging
    
---
apiVersion: v1
kind: Namespace
metadata:
  name: monitoring
  labels:
    environment: monitoring
    
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: production-quota
  namespace: production
spec:
  hard:
    requests.cpu: "100"
    requests.memory: 200Gi
    limits.cpu: "200"
    limits.memory: 400Gi
    persistentvolumeclaims: "10"
```

### 3.3 Service Mesh (Istio)

```yaml
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
metadata:
  name: control-plane
spec:
  profile: production
  values:
    pilot:
      autoscaleEnabled: true
      autoscaleMin: 2
      autoscaleMax: 5
      resources:
        requests:
          cpu: 500m
          memory: 2048Mi
    
    global:
      proxy:
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 200m
            memory: 256Mi
    
    gateways:
      istio-ingressgateway:
        autoscaleEnabled: true
        autoscaleMin: 2
        autoscaleMax: 10
```

## 4. データベースインフラストラクチャ

### 4.1 PostgreSQL クラスター

```yaml
# PostgreSQL High Availability Setup
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: postgres-cluster
spec:
  instances: 3
  
  postgresql:
    version: "16"
    parameters:
      max_connections: "200"
      shared_buffers: "256MB"
      effective_cache_size: "1GB"
      work_mem: "4MB"
      maintenance_work_mem: "64MB"
      checkpoint_completion_target: "0.9"
      wal_buffers: "16MB"
      default_statistics_target: "100"
      random_page_cost: "1.1"
      effective_io_concurrency: "200"
      
  bootstrap:
    initdb:
      database: tonebridge
      owner: tonebridge
      
  storage:
    size: 100Gi
    storageClass: fast-ssd
    
  monitoring:
    enabled: true
    
  backup:
    enabled: true
    retentionPolicy: "30d"
    s3:
      bucket: tonebridge-backups
      path: /postgres
      region: us-west-2
```

### 4.2 Redis クラスター

```yaml
apiVersion: redis.redis.opstreelabs.in/v1beta1
kind: RedisCluster
metadata:
  name: redis-cluster
spec:
  clusterSize: 6
  redisLeader:
    replicas: 3
    
  redisFollower:
    replicas: 3
    
  redisConfig:
    maxmemory: "2gb"
    maxmemory-policy: "allkeys-lru"
    appendonly: "yes"
    appendfsync: "everysec"
    
  storage:
    volumeClaimTemplate:
      spec:
        accessModes:
        - ReadWriteOnce
        resources:
          requests:
            storage: 10Gi
        storageClassName: fast-ssd
```

## 5. コンテナレジストリ

### 5.1 ECR/GCR/ACR構成

```bash
# レジストリ構成
registries:
  production:
    url: 123456789.dkr.ecr.us-west-2.amazonaws.com
    repositories:
      - tonebridge/api-gateway
      - tonebridge/llm-service
      - tonebridge/auth-service
      - tonebridge/analytics-service
      
  staging:
    url: 123456789.dkr.ecr.us-west-2.amazonaws.com
    repositories:
      - tonebridge-staging/*
      
  development:
    url: gcr.io/tonebridge-dev
    repositories:
      - dev/*
```

### 5.2 イメージスキャニング

```yaml
# Trivy Security Scanning
apiVersion: batch/v1
kind: Job
metadata:
  name: image-security-scan
spec:
  template:
    spec:
      containers:
      - name: trivy
        image: aquasec/trivy:latest
        command:
          - trivy
          - image
          - --severity
          - HIGH,CRITICAL
          - --no-progress
          - --format
          - json
          - --output
          - /tmp/scan-results.json
          - $(IMAGE_NAME)
        env:
        - name: IMAGE_NAME
          value: "tonebridge/api-gateway:latest"
```

## 6. CI/CDインフラストラクチャ

### 6.1 GitOps (ArgoCD)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: tonebridge-production
  namespace: argocd
spec:
  project: default
  
  source:
    repoURL: https://github.com/tonebridge/k8s-manifests
    targetRevision: main
    path: environments/production
    
  destination:
    server: https://kubernetes.default.svc
    namespace: production
    
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
      allowEmpty: false
    syncOptions:
    - Validate=true
    - CreateNamespace=false
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
```

### 6.2 Jenkins Pipeline

```groovy
pipeline {
    agent {
        kubernetes {
            yaml """
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: docker
    image: docker:dind
    securityContext:
      privileged: true
  - name: kubectl
    image: bitnami/kubectl:latest
    command:
    - cat
    tty: true
"""
        }
    }
    
    environment {
        DOCKER_REGISTRY = credentials('docker-registry')
        KUBECONFIG = credentials('kubeconfig')
    }
    
    stages {
        stage('Build') {
            steps {
                container('docker') {
                    sh '''
                        docker build -t ${DOCKER_REGISTRY}/tonebridge:${BUILD_NUMBER} .
                        docker push ${DOCKER_REGISTRY}/tonebridge:${BUILD_NUMBER}
                    '''
                }
            }
        }
        
        stage('Security Scan') {
            steps {
                sh '''
                    trivy image ${DOCKER_REGISTRY}/tonebridge:${BUILD_NUMBER}
                '''
            }
        }
        
        stage('Deploy to Staging') {
            steps {
                container('kubectl') {
                    sh '''
                        kubectl set image deployment/api-gateway \
                            api-gateway=${DOCKER_REGISTRY}/tonebridge:${BUILD_NUMBER} \
                            -n staging
                        kubectl rollout status deployment/api-gateway -n staging
                    '''
                }
            }
        }
        
        stage('Integration Tests') {
            steps {
                sh '''
                    npm run test:integration
                '''
            }
        }
        
        stage('Deploy to Production') {
            when {
                branch 'main'
            }
            steps {
                input 'Deploy to production?'
                container('kubectl') {
                    sh '''
                        kubectl set image deployment/api-gateway \
                            api-gateway=${DOCKER_REGISTRY}/tonebridge:${BUILD_NUMBER} \
                            -n production --record
                        kubectl rollout status deployment/api-gateway -n production
                    '''
                }
            }
        }
    }
    
    post {
        success {
            slackSend(
                color: 'good',
                message: "Deployment successful: ${env.JOB_NAME} - ${env.BUILD_NUMBER}"
            )
        }
        failure {
            slackSend(
                color: 'danger',
                message: "Deployment failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}"
            )
        }
    }
}
```

## 7. モニタリングインフラストラクチャ

### 7.1 Prometheus Stack

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
      
    alerting:
      alertmanagers:
      - static_configs:
        - targets:
          - alertmanager:9093
          
    rule_files:
      - /etc/prometheus/rules/*.yml
      
    scrape_configs:
    - job_name: 'kubernetes-apiservers'
      kubernetes_sd_configs:
      - role: endpoints
      scheme: https
      tls_config:
        ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
      bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
      
    - job_name: 'kubernetes-nodes'
      kubernetes_sd_configs:
      - role: node
      
    - job_name: 'kubernetes-pods'
      kubernetes_sd_configs:
      - role: pod
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
```

### 7.2 ELK Stack

```yaml
apiVersion: elasticsearch.k8s.elastic.co/v1
kind: Elasticsearch
metadata:
  name: elasticsearch
spec:
  version: 8.11.0
  nodeSets:
  - name: master
    count: 3
    config:
      node.roles: ["master"]
    volumeClaimTemplates:
    - metadata:
        name: elasticsearch-data
      spec:
        accessModes:
        - ReadWriteOnce
        resources:
          requests:
            storage: 10Gi
        storageClassName: fast-ssd
            
  - name: data
    count: 3
    config:
      node.roles: ["data", "ingest"]
    volumeClaimTemplates:
    - metadata:
        name: elasticsearch-data
      spec:
        accessModes:
        - ReadWriteOnce
        resources:
          requests:
            storage: 100Gi
        storageClassName: fast-ssd
```

### 7.3 Grafana Dashboards

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-dashboards
data:
  infrastructure.json: |
    {
      "dashboard": {
        "title": "Infrastructure Overview",
        "panels": [
          {
            "title": "Cluster CPU Usage",
            "targets": [{
              "expr": "sum(rate(container_cpu_usage_seconds_total[5m])) by (node)"
            }]
          },
          {
            "title": "Memory Usage",
            "targets": [{
              "expr": "sum(container_memory_usage_bytes) by (node)"
            }]
          },
          {
            "title": "Network I/O",
            "targets": [{
              "expr": "sum(rate(container_network_receive_bytes_total[5m]))"
            }]
          },
          {
            "title": "Disk Usage",
            "targets": [{
              "expr": "sum(node_filesystem_size_bytes - node_filesystem_free_bytes) by (instance)"
            }]
          }
        ]
      }
    }
```

## 8. セキュリティインフラストラクチャ

### 8.1 Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-gateway-policy
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: api-gateway
  policyTypes:
  - Ingress
  - Egress
  
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: istio-system
    ports:
    - protocol: TCP
      port: 8080
      
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: llm-service
    ports:
    - protocol: TCP
      port: 8000
  - to:
    - podSelector:
        matchLabels:
          app: auth-service
    ports:
    - protocol: TCP
      port: 8001
```

### 8.2 Secrets Management (Vault)

```yaml
apiVersion: vault.hashicorp.com/v1alpha1
kind: VaultAuth
metadata:
  name: tonebridge-auth
spec:
  method: kubernetes
  mount: kubernetes
  kubernetes:
    role: tonebridge
    serviceAccount: tonebridge-sa
    
---
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: vault-secrets
spec:
  provider: vault
  parameters:
    vaultAddress: "http://vault:8200"
    roleName: "tonebridge"
    objects: |
      - objectName: "database-password"
        secretPath: "secret/data/database"
        secretKey: "password"
      - objectName: "jwt-secret"
        secretPath: "secret/data/jwt"
        secretKey: "secret"
      - objectName: "openai-api-key"
        secretPath: "secret/data/openai"
        secretKey: "api-key"
```

### 8.3 Pod Security Policies

```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: restricted
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  hostNetwork: false
  hostIPC: false
  hostPID: false
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  supplementalGroups:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
  readOnlyRootFilesystem: true
```

## 9. 災害復旧インフラストラクチャ

### 9.1 マルチリージョン構成

```yaml
regions:
  primary:
    name: us-west-2
    provider: AWS
    components:
      - kubernetes_cluster
      - postgresql_primary
      - redis_primary
      - s3_buckets
      
  secondary:
    name: us-east-1
    provider: AWS
    components:
      - kubernetes_cluster
      - postgresql_replica
      - redis_replica
      - s3_replicated
      
  dr:
    name: europe-west1
    provider: GCP
    components:
      - kubernetes_cluster_standby
      - postgresql_backup
      - object_storage_backup
```

### 9.2 バックアップストレージ

```bash
# S3 Backup Configuration
aws s3api create-bucket \
    --bucket tonebridge-backups \
    --region us-west-2 \
    --create-bucket-configuration LocationConstraint=us-west-2

# Versioning
aws s3api put-bucket-versioning \
    --bucket tonebridge-backups \
    --versioning-configuration Status=Enabled

# Lifecycle Policy
aws s3api put-bucket-lifecycle-configuration \
    --bucket tonebridge-backups \
    --lifecycle-configuration file://lifecycle.json

# Cross-Region Replication
aws s3api put-bucket-replication \
    --bucket tonebridge-backups \
    --replication-configuration file://replication.json
```

## 10. コスト最適化

### 10.1 リソース最適化

```yaml
# Cluster Autoscaler
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cluster-autoscaler
  namespace: kube-system
spec:
  template:
    spec:
      containers:
      - image: k8s.gcr.io/autoscaling/cluster-autoscaler:v1.28.0
        name: cluster-autoscaler
        command:
        - ./cluster-autoscaler
        - --v=4
        - --stderrthreshold=info
        - --cloud-provider=aws
        - --skip-nodes-with-local-storage=false
        - --expander=least-waste
        - --node-group-auto-discovery=asg:tag=k8s.io/cluster-autoscaler/enabled,k8s.io/cluster-autoscaler/tonebridge-production
```

### 10.2 Spot Instances

```yaml
apiVersion: karpenter.sh/v1alpha5
kind: Provisioner
metadata:
  name: spot-provisioner
spec:
  requirements:
    - key: karpenter.sh/capacity-type
      operator: In
      values: ["spot"]
    - key: kubernetes.io/arch
      operator: In
      values: ["amd64"]
      
  limits:
    resources:
      cpu: 1000
      memory: 1000Gi
      
  provider:
    instanceTypes:
    - c5.large
    - c5.xlarge
    - c5.2xlarge
    - c5a.large
    - c5a.xlarge
    
  ttlSecondsAfterEmpty: 30
  
  taints:
  - key: spot
    value: "true"
    effect: NoSchedule
```

## 11. Infrastructure as Code

### 11.1 Terraform構成

```hcl
# main.tf
terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
  }
  
  backend "s3" {
    bucket = "tonebridge-terraform-state"
    key    = "production/infrastructure.tfstate"
    region = "us-west-2"
    encrypt = true
    dynamodb_table = "terraform-state-lock"
  }
}

module "vpc" {
  source = "./modules/vpc"
  
  cidr_block = "10.0.0.0/16"
  availability_zones = ["us-west-2a", "us-west-2b", "us-west-2c"]
  
  public_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  private_subnets = ["10.0.10.0/24", "10.0.11.0/24", "10.0.12.0/24"]
  database_subnets = ["10.0.20.0/24", "10.0.21.0/24", "10.0.22.0/24"]
  
  enable_nat_gateway = true
  enable_vpn_gateway = true
  enable_dns_hostnames = true
  enable_dns_support = true
  
  tags = {
    Environment = "production"
    Project = "tonebridge"
  }
}

module "eks" {
  source = "./modules/eks"
  
  cluster_name = "tonebridge-production"
  cluster_version = "1.28"
  
  vpc_id = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
  
  node_groups = {
    system = {
      desired_capacity = 2
      max_capacity = 5
      min_capacity = 2
      instance_types = ["t3.medium"]
    }
    
    application = {
      desired_capacity = 3
      max_capacity = 20
      min_capacity = 3
      instance_types = ["c5.xlarge"]
    }
  }
}

module "rds" {
  source = "./modules/rds"
  
  identifier = "tonebridge-postgres"
  engine = "postgres"
  engine_version = "16.1"
  
  instance_class = "db.r5.2xlarge"
  allocated_storage = 100
  storage_encrypted = true
  
  vpc_id = module.vpc.vpc_id
  subnet_ids = module.vpc.database_subnets
  
  backup_retention_period = 30
  preferred_backup_window = "03:00-04:00"
  preferred_maintenance_window = "sun:04:00-sun:05:00"
  
  enabled_cloudwatch_logs_exports = ["postgresql"]
}
```

## 12. パフォーマンスチューニング

### 12.1 カーネルパラメータ

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: sysctl-config
data:
  sysctl.conf: |
    # Network tuning
    net.core.somaxconn = 65535
    net.ipv4.tcp_max_syn_backlog = 8192
    net.ipv4.tcp_tw_reuse = 1
    net.ipv4.tcp_fin_timeout = 30
    net.ipv4.ip_local_port_range = 10000 65000
    
    # Memory tuning
    vm.max_map_count = 262144
    vm.swappiness = 1
    
    # File system tuning
    fs.file-max = 2097152
    fs.nr_open = 1048576
```

### 12.2 リソース最適化

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-resources
  namespace: production
spec:
  hard:
    requests.cpu: "100"
    requests.memory: 200Gi
    limits.cpu: "200"
    limits.memory: 400Gi
    
---
apiVersion: v1
kind: LimitRange
metadata:
  name: resource-limits
  namespace: production
spec:
  limits:
  - max:
      cpu: "2"
      memory: 4Gi
    min:
      cpu: 100m
      memory: 128Mi
    default:
      cpu: 500m
      memory: 512Mi
    defaultRequest:
      cpu: 200m
      memory: 256Mi
    type: Container
```

## まとめ

ToneBridgeのインフラストラクチャは、クラウドネイティブの原則に基づいて設計され、高可用性、拡張性、セキュリティを実現しています。Infrastructure as Codeにより、一貫性のある環境構築と迅速なデプロイメントが可能です。継続的な監視と最適化により、コスト効率的な運用を維持します。