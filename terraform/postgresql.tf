resource "google_sql_database_instance" "postgres" {
  name             = "${var.db_instance_name}-${var.environment}"
  region           = var.region
  database_version = var.db_version

  settings {
    tier = var.db_tier

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
    }

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
    }
  }

  deletion_protection = true

  depends_on = [
    google_project_service.required,
    google_service_networking_connection.private_vpc_connection,
  ]
}

resource "google_sql_database" "incidents" {
  name     = var.db_name
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "app_user" {
  name     = var.db_user
  instance = google_sql_database_instance.postgres.name
  password = var.db_password
}

output "db_instance_connection_name" {
  description = "Cloud SQL instance connection name, for use with the Cloud SQL Auth Proxy"
  value       = google_sql_database_instance.postgres.connection_name
}

output "db_private_ip" {
  description = "Private IP address of the Cloud SQL instance"
  value       = google_sql_database_instance.postgres.private_ip_address
}

output "database_url" {
  description = "Postgres connection string for the API's DATABASE_URL"
  value       = "postgresql://${var.db_user}:${var.db_password}@${google_sql_database_instance.postgres.private_ip_address}:5432/${var.db_name}"
  sensitive   = true
}
