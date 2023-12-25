terraform {
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
    }
  }
  required_version = ">= 0.13"
}

provider "yandex" {
  service_account_key_file = "key.json"
  cloud_id                 = var.cloud_id
  folder_id                = var.folder_id
  zone                     = var.region_id
}

resource "yandex_iam_service_account" "sa" {
  name = var.service_account_name
}

resource "yandex_resourcemanager_folder_iam_member" "sa-editor" {
  folder_id = var.folder_id
  role      = "storage.editor"
  member    = "serviceAccount:${yandex_iam_service_account.sa.id}"
}

resource "yandex_iam_service_account_static_access_key" "sa-static-key" {
  service_account_id = yandex_iam_service_account.sa.id
}

resource "yandex_storage_bucket" "photo" {
  access_key = yandex_iam_service_account_static_access_key.sa-static-key.access_key
  secret_key = yandex_iam_service_account_static_access_key.sa-static-key.secret_key
  bucket     = var.bucket_name_photo
}

resource "yandex_storage_bucket" "faces" {
  access_key = yandex_iam_service_account_static_access_key.sa-static-key.access_key
  secret_key = yandex_iam_service_account_static_access_key.sa-static-key.secret_key
  bucket     = var.bucket_name_faces
}

data "archive_file" "cut_zip_1" {
  type        = "zip"
  source_file  = "face-cut.py"
  output_path = "result_cut.zip"
}

resource "yandex_function" "face" {
    name               = var.face_cut_func_name
    user_hash          = "first-function"
    runtime            = "python37"
    entrypoint         = "face-cut.handler"
    memory             = "128"
    execution_timeout  = "10"
    service_account_id = yandex_iam_service_account.sa.id
    tags               = ["my_tag"]
    folder_id                = var.folder_id

    content {
        zip_filename = "result_cut.zip"
    }

    environment = {
      AWS_ACCESS_KEY_ID = var.aws_access_key_id
      AWS_ACCESS_KEY = var.aws_access_key
      AWS_REGION = var.region_id
      FACES_BUCKET_NAME = var.bucket_name_faces
      PHOTO_BUCKET_NAME = var.bucket_name_photo
      USER_STORAGE_URL = var.user_storage_url
      TABLE_NAME = var.table_name
    }
}

data "archive_file" "detection_zip_1" {
  type        = "zip"
  source_file  = "face-detection.py"
  output_path = "result_detection.zip"
}

resource "yandex_function" "face-detection" {
    name               = var.face_detection_func_name
    user_hash          = "first-function"
    runtime            = "python37"
    entrypoint         = "face-detection.handler"
    memory             = "128"
    execution_timeout  = "10"
    service_account_id = yandex_iam_service_account.sa.id
    tags               = ["my_tag"]
    folder_id                = var.folder_id

    content {
        zip_filename = "result_detection.zip"
    }

    environment = {
      QUEUE_URL = var.queue_url
      AWS_ACCESS_KEY_ID = var.aws_access_key_id
      AWS_ACCESS_KEY = var.aws_access_key
      AWS_REGION = var.region_id
      FACES_BUCKET_NAME = var.bucket_name_faces
      PHOTO_BUCKET_NAME = var.bucket_name_photo
      USER_STORAGE_URL = var.user_storage_url
      TABLE_NAME = var.table_name
      TOKEN = var.token
    }
}

resource "yandex_message_queue" "vvot01-task" {
  name                        = "vvot01-task"
  visibility_timeout_seconds  = 30
  receive_wait_time_seconds   = 20
  message_retention_seconds   = 345600
  access_key                  = yandex_iam_service_account_static_access_key.sa-static-key.access_key
  secret_key                  = yandex_iam_service_account_static_access_key.sa-static-key.secret_key
}

resource "yandex_ydb_database_serverless" "vvot01-db-photo-face" {
  name                = var.bd_name
  folder_id = var.folder_id
  deletion_protection = true

  serverless_database {
    enable_throttling_rcu_limit = false
    provisioned_rcu_limit       = 10
    storage_size_limit          = 5
    throttling_rcu_limit        = 0
  }
}

resource "yandex_api_gateway" "vvot01-apigw" {
  name = var.api_gateway_name
  folder_id = var.folder_id
  spec = <<-EOT
    openapi: 3.0.0
    info:
      version: 1.0.0
      title: Test API
    paths:
      /{file}:
        get:
          summary: Serve static file from Yandex Cloud Object Storage
          parameters:
            - name: file
              in: path
              required: true
              schema:
                type: string

          x-yc-apigateway-integration:
              type: object_storage
              bucket: ${var.bucket_name_faces}
              object: '{file}'
              error_object: error.html
              service_account_id: ${yandex_iam_service_account.sa.id}
  EOT
}

data "archive_file" "detection_zip_1" {
  type        = "zip"
  source_file  = "bot.py"
  output_path = "result_bot.zip"
}

resource "yandex_function" "vvot01_2023_bot" {
  name               = "vvot13-2023-boot"
  user_hash          = "4934cfc4-636d-470f-a649-1ddfc6b494ae"
  runtime            = "python311"
  entrypoint         = "bot.handler"
  memory             = "128"
  execution_timeout  = "60"
  service_account_id = yandex_iam_service_account.sa.id
  tags               = ["my_tag"]

  content {
        zip_filename = "result_bot.zip"
  }

  environment = {
    USER_STORAGE_URL=var.user_storage_url
    AWS_ACCESS_KEY_ID=var.aws_access_key_id
    AWS_SECRET_ACCESS_KEY=var.aws_access_key
    API_GATEWAY=var.api_gateway_name
    TELEGRAM_BOT_TOKEN=var.tgkey
  }
}

resource "yandex_function_iam_binding" "function-boot" {
  function_id = yandex_function.vvot01_2023_bot.id
  role        = "functions.functionInvoker"
  members = [
    "system:allUsers",
  ]
}

data "http" "webhook" {
  url = "https://api.telegram.org/bot${var.tgkey}/setWebhook?url=https://functions.yandexcloud.net/${yandex_function.vvot13-2023-boot.id}"
}
