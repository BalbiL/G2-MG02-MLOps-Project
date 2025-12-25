
variable "supabase_url" {
  description = "L'URL de votre projet Supabase"
  type        = string
  sensitive   = true # Masque la valeur dans les logs Terraform
}

variable "supabase_key" {
  description = "La clé API de Supabase"
  type        = string
  sensitive   = true
}