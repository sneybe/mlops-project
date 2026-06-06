terraform {
  required_providers {
    multipass = {
      source  = "larstobi/multipass"
      version = "~> 1.4"
    }
  }
}

provider "multipass" {}

resource "multipass_instance" "devops" {
  name = "devops"
}

resource "multipass_instance" "k8s" {
  name = "k8s"
}

resource "multipass_instance" "monitoring" {
  name = "monitoring"
}
