provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "user_uploads" {
  bucket = "my-app-user-uploads"
  acl    = "public-read"
  tags = { Name = "user-uploads" }
}

resource "aws_db_instance" "main" {
  identifier        = "main-db"
  engine            = "mysql"
  engine_version    = "8.0"
  instance_class    = "db.r5.4xlarge"
  allocated_storage = 100
  username          = "admin"
  password          = "hardcoded_password_123"
  skip_final_snapshot = true
  multi_az          = false
  tags = { Environment = "production" }
}

resource "aws_iam_role_policy" "app_policy" {
  name = "app-policy"
  role = aws_iam_role.app_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = "*", Resource = "*" }]
  })
}

resource "aws_iam_role" "app_role" {
  name = "app-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{ Action = "sts:AssumeRole", Effect = "Allow", Principal = { Service = "ec2.amazonaws.com" } }]
  })
}

resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.large"
  monitoring    = false
  associate_public_ip_address = true
  tags = { Name = "web-server", Environment = "production" }
}

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = { Name = "main-vpc" }
}
