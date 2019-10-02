# -------------------------------------------------------------
#  AWS PROVIDER
# -------------------------------------------------------------

provider "aws" {
  version = "~> 2.19"
  profile = "prod" # profile name in /aws/configure
  region  = "ap-southeast-2"
}

# S3 config for Terraform
terraform {
  backend "s3" {
    bucket         = "prod-terraform"
    key            = "backups/prod/-prod-backups.tfstate"
    encrypt        = "true"
    profile        = "prod"
    region         = "ap-southeast-2"
    dynamodb_table = "terraform-lock"
  }
}

# -------------------------------------------------------------
#  SOURCE TO MODULE
# -------------------------------------------------------------

module "backups" {
  source      = "../../../global/services/aws-backups-module"
  account     = "prod"
  backup_role = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup"
} 