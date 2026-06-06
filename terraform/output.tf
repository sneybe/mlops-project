output "devops_ip" {
  value       = multipass_instance.devops.ipv4
  description = "IP de la VM devops"
}

output "k8s_ip" {
  value       = multipass_instance.k8s.ipv4
  description = "IP de la VM k8s"
}

output "monitoring_ip" {
  value       = multipass_instance.monitoring.ipv4
  description = "IP de la VM monitoring"
}
