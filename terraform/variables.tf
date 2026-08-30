variable "project_id" {
  description = "GCP project ID to deploy into"
  type        = string
}

variable "region" {
  description = "GCP region for regional resources (GKE, subnet, Cloud SQL)"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP zone for zonal resources"
  type        = string
  default     = "us-central1-a"
}

variable "environment" {
  description = "Deployment environment name, used as a resource name suffix"
  type        = string
  default     = "dev"
}

# --- Networking ---

variable "network_name" {
  description = "Name of the VPC network created for this platform"
  type        = string
  default     = "incident-response-network"
}

variable "subnet_cidr" {
  description = "CIDR range for the GKE subnet"
  type        = string
  default     = "10.10.0.0/20"
}

variable "pods_cidr" {
  description = "Secondary CIDR range for GKE pod IPs"
  type        = string
  default     = "10.20.0.0/16"
}

variable "services_cidr" {
  description = "Secondary CIDR range for GKE service IPs"
  type        = string
  default     = "10.30.0.0/20"
}

# --- GKE ---

variable "gke_cluster_name" {
  description = "Name of the GKE cluster"
  type        = string
  default     = "incident-response-cluster"
}

variable "gke_node_count" {
  description = "Number of nodes in the primary GKE node pool"
  type        = number
  default     = 2
}

variable "gke_machine_type" {
  description = "Machine type for GKE nodes"
  type        = string
  default     = "e2-standard-2"
}

# --- Cloud SQL ---

variable "db_instance_name" {
  description = "Name of the Cloud SQL Postgres instance"
  type        = string
  default     = "incident-response-db"
}

variable "db_tier" {
  description = "Cloud SQL machine tier"
  type        = string
  default     = "db-custom-1-3840"
}

variable "db_version" {
  description = "Cloud SQL Postgres engine version"
  type        = string
  default     = "POSTGRES_16"
}

variable "db_name" {
  description = "Name of the application database"
  type        = string
  default     = "incidents"
}

variable "db_user" {
  description = "Application database username"
  type        = string
  default     = "incidents_user"
}

variable "db_password" {
  description = "Application database password (supply via tfvars or CI secret, never commit a default)"
  type        = string
  sensitive   = true
}
