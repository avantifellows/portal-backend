# terraform init -backend-config="key=portal-backend/staging/terraform.tfstate"
terraform {
  backend "s3" {
    bucket  = "111766607077-dbservice-test-terraform-state"
    region  = "ap-south-1"
    encrypt = true
  }
}
