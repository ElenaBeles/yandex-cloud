variable "cloud_id" {
  type        = string
}

variable "folder_id" {
  type        = string
}

variable "region_id" {
  type        = string
}

variable "folder_api_id" {
  type        = string
}


variable "api_gateway" {
  type        = string
  description = "Function memory"
}

variable "bucket_name" {
  type        = string
  description = "Function memory"
}

variable "account_id" {
  type        = string
  description = "Function memory"
}

variable "bd_name" {
  type        = string
}

variable "face_cut_func_name" {
  type        = string
}

variable "face_detection_func_name" {
  type        = string
}

variable "messages_queue_name" {
  type        = string
}

variable "token" {
  type        = string
}

variable "queue_url" {
  type        = string
}

variable "aws_access_key_id" {
  type        = string
}

variable "aws_access_key" {
  type        = string
}

variable "aws_region" {
  type        = string
}

variable "faces_bucket_name" {
  type        = string
}

variable "photo_bucket_name" {
  type        = string
}

variable "user_storage_url" {
  type        = string
}

variable "table_name" {
  type        = string
}

variable "service_account_name" {
  type        = string
}

variable "bucket_name_photo" {
  type        = string
}

variable "bucket_name_faces" {
  type        = string
}