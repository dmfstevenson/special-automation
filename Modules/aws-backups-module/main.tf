# -------------------------------------------------------------
# AWS Backup stanza - Create Vault /  Backup Plan / Jobs / and RDS version
# -------------------------------------------------------------

data "aws_kms_key" "backup" {
  key_id = "alias/aws/backup"
}

# -------------------------------------------------------------
# IAM ROLE
# -------------------------------------------------------------

resource "aws_iam_role" "AWSBackupServiceRolePolicyForBackup" {
  name               = "AWSBackupServiceRolePolicyForBackup"
  assume_role_policy = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": ["sts:AssumeRole"],
      "Effect": "allow",
      "Principal": {
        "Service": ["backup.amazonaws.com"]
      }
    }
  ]
}
POLICY
}

resource "aws_iam_role_policy_attachment" "AWSBackupServiceRolePolicyForBackup" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup"
  role       = "${aws_iam_role.AWSBackupServiceRolePolicyForBackup.name}"
}

resource "aws_iam_role_policy_attachment" "AWSKeyManagementServicePowerUser" {
  policy_arn = "arn:aws:iam::aws:policy/AWSKeyManagementServicePowerUser"
  role       = "${aws_iam_role.AWSBackupServiceRolePolicyForBackup.name}"
}

# -------------------------------------------------------------
# EBS STANZA
# -------------------------------------------------------------

resource "aws_backup_plan" "plan" {
  name = "${var.account}-backup-plan"

  rule {
    rule_name         = "${var.account}-backup-rule"
    target_vault_name = "${aws_backup_vault.vault.name}"
    schedule          = "cron(0 16 ? * FRI *)" # 4PM UTC (Roughly 3AM AEST)
    start_window      = "60"
    completion_window = "480"
    lifecycle {
      cold_storage_after = "1"
      delete_after       = "91"
    }
  }
}

resource "aws_backup_vault" "vault" {
  name = "${var.account}_backup_vault"
  kms_key_arn = "${data.aws_kms_key.backup.arn}"
}

resource "aws_backup_selection" "selection" {

  iam_role_arn = "${aws_iam_role.AWSBackupServiceRolePolicyForBackup.arn}"
  name         = "${var.account}-backup-selection"
  plan_id      = "${aws_backup_plan.plan.id}"

  selection_tag {
    type  = "STRINGEQUALS"
    key   = "Backup"
    value = "Yes"
  }
}

# -------------------------------------------------------------
# RDS STANZA
# -------------------------------------------------------------

resource "aws_backup_plan" "planrds" {
  name = "${var.account}-backup-planrds"

  rule {
    rule_name         = "${var.account}-backup-rulerds"
    target_vault_name = "${aws_backup_vault.vaultrds.name}"
    schedule          = "cron(0 16 ? * FRI *)"  # 4PM UTC (Roughly 3AM AEST)
    start_window      = "60"
    completion_window = "480"
    lifecycle {
      cold_storage_after = "1"
      delete_after       = "91"
    }
  }
}

resource "aws_backup_vault" "vaultrds" {
  name = "${var.account}_backup_vaultrds"
}

resource "aws_backup_selection" "selectionrds" {
  iam_role_arn = "${aws_iam_role.AWSBackupServiceRolePolicyForBackup.arn}"
  name         = "${var.account}-backup-selectionrds"
  plan_id      = "${aws_backup_plan.planrds.id}"

  selection_tag {
    type  = "STRINGEQUALS"
    key   = "BackupRds"
    value = "Yes"
  }
}