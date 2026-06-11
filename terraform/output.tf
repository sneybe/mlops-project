output "devops_ip" {
  value = multipass_instance.devops.ipv4
}

output "k8s_ip" {
  value = multipass_instance.k8s.ipv4
}

output "monitoring_ip" {
  value = multipass_instance.monitoring.ipv4
}
