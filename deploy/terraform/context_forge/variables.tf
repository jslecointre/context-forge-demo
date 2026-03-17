# ----------------------------
# IBM Cloud
# ----------------------------
variable "ibmcloud_api_key" {
  type        = string
  description = "IBM Cloud API Key"
  default     = ""
  sensitive   = true
}

variable "region" {
  description = "Region where Code Engine project exists"
  type        = string
  default     = "us-south"
}

variable "ce_project_name" {
  description = "Code Engine project name. Overrides the auto-derived 'ce-<resource_group>' name when set."
  type        = string
  default     = ""
}

# ----------------------------
# Container Registry
# ----------------------------
variable "cr_registry_server" {
  description = "Container Registry server hostname (e.g. us.icr.io)"
  type        = string
  default     = "us.icr.io"
}

variable "cr_namespace" {
  description = "Container Registry namespace where the mcp-context-forge-plugin image is stored"
  type        = string
  default     = ""
}

variable "image_name" {
  description = "mcp-context-forge-plugin image name in the Container Registry"
  type        = string
  default     = "mcp-context-forge-plugin"
}

# ----------------------------
# App Configuration
# ----------------------------
variable "app_name" {
  description = "Code Engine app name for the mcp-context-forge-plugin service"
  type        = string
  default     = "mcp-context-forge-plugin"
}

variable "app_port" {
  description = "Listening port for the mcp-context-forge-plugin app (CONTEXT_FORGE_PORT)"
  type        = number
  default     = 4444
}

# ----------------------------
# Redis
# ----------------------------
variable "redis_app_name" {
  description = "Code Engine app name for the Redis service"
  type        = string
  default     = "redis"
}

variable "redis_url" {
  description = "Redis connection URL. Defaults to internal Code Engine URL (redis://<redis_app_name>:6379). Override with IBM Databases for Redis or external Redis URL for production."
  type        = string
  default     = ""
}

# ----------------------------
# Authentication
# ----------------------------
variable "basic_auth_user" {
  description = "HTTP Basic Auth username (BASIC_AUTH_USER)"
  type        = string
  default     = "admin"
}

variable "basic_auth_password" {
  description = "HTTP Basic Auth password (BASIC_AUTH_PASSWORD)"
  type        = string
  default     = "changeme"
  sensitive   = true
}

variable "jwt_secret_key" {
  description = "JWT signing secret key (JWT_SECRET_KEY)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "auth_encryption_secret" {
  description = "Encryption salt/secret for auth tokens (AUTH_ENCRYPTION_SECRET)"
  type        = string
  default     = ""
  sensitive   = true
}

# ----------------------------
# Platform Admin
# ----------------------------
variable "platform_admin_email" {
  description = "Platform administrator email address (PLATFORM_ADMIN_EMAIL)"
  type        = string
  default     = "admin@example.com"
}

variable "platform_admin_password" {
  description = "Platform administrator password (PLATFORM_ADMIN_PASSWORD)"
  type        = string
  default     = "changeme"
  sensitive   = true
}

variable "default_user_password" {
  description = "Default password for newly created users (DEFAULT_USER_PASSWORD)"
  type        = string
  default     = "changeme"
  sensitive   = true
}

# ----------------------------
# Token Settings
# ----------------------------
variable "require_jti" {
  description = "Require JWT ID (jti) claim in tokens (REQUIRE_JTI)"
  type        = string
  default     = "true"
}

variable "require_token_expiration" {
  description = "Require token expiration claim (REQUIRE_TOKEN_EXPIRATION)"
  type        = string
  default     = "true"
}

variable "public_registration_enabled" {
  description = "Allow public user self-registration (PUBLIC_REGISTRATION_ENABLED)"
  type        = string
  default     = "false"
}

variable "allow_public_visibility" {
  description = "Allow public visibility of resources (ALLOW_PUBLIC_VISIBILITY)"
  type        = string
  default     = "true"
}

# ----------------------------
# Network
# ----------------------------
variable "host" {
  description = "Bind address for the application (HOST)"
  type        = string
  default     = "0.0.0.0"
}

variable "app_domain" {
  description = "Public URL of this app (APP_DOMAIN). Defaults to http://localhost for first deploy; update to the Code Engine endpoint afterwards."
  type        = string
  default     = "http://localhost"
}

# ----------------------------
# Gateway Features
# ----------------------------
variable "mcpgateway_ui_enabled" {
  description = "Enable the MCP Gateway web UI (MCPGATEWAY_UI_ENABLED)"
  type        = string
  default     = "true"
}

variable "mcpgateway_admin_api_enabled" {
  description = "Enable the MCP Gateway admin API (MCPGATEWAY_ADMIN_API_ENABLED)"
  type        = string
  default     = "true"
}

variable "mcpgateway_ws_relay_enabled" {
  description = "Enable WebSocket relay (MCPGATEWAY_WS_RELAY_ENABLED)"
  type        = string
  default     = "false"
}

variable "mcpgateway_reverse_proxy_enabled" {
  description = "Enable reverse proxy mode (MCPGATEWAY_REVERSE_PROXY_ENABLED)"
  type        = string
  default     = "false"
}

# ----------------------------
# SSRF Protection
# ----------------------------
variable "ssrf_allow_localhost" {
  description = "Allow SSRF requests to localhost (SSRF_ALLOW_LOCALHOST)"
  type        = string
  default     = "true"
}

variable "ssrf_allow_private_networks" {
  description = "Allow SSRF requests to private networks (SSRF_ALLOW_PRIVATE_NETWORKS)"
  type        = string
  default     = "true"
}

variable "ssrf_dns_fail_closed" {
  description = "Fail closed on DNS resolution errors for SSRF checks (SSRF_DNS_FAIL_CLOSED)"
  type        = string
  default     = "false"
}

# ----------------------------
# Security
# ----------------------------
variable "secure_cookies" {
  description = "Enable Secure flag on cookies – set to true when serving over HTTPS (SECURE_COOKIES)"
  type        = string
  default     = "false"
}

variable "dangerous_patterns" {
  description = "JSON array of regex patterns blocked as dangerous input (DANGEROUS_PATTERNS)"
  type        = list(string)
  default = [
    "[;&|`$(){}\\[\\]<>]",
    "\\.\\.[\\\\//]",
    "[\\x00-\\x1f\\x7f-\\x9f]",
    "(?i)(drop|delete|insert|update|select)\\s+(table|from|into|where)"
  ]
}

# ----------------------------
# Validation / Audit
# ----------------------------
variable "experimental_validate_io" {
  description = "Enable experimental I/O validation (EXPERIMENTAL_VALIDATE_IO)"
  type        = string
  default     = "false"
}

variable "validation_middleware_enabled" {
  description = "Enable validation middleware (VALIDATION_MIDDLEWARE_ENABLED)"
  type        = string
  default     = "false"
}

variable "permission_audit_enabled" {
  description = "Enable permission audit logging (PERMISSION_AUDIT_ENABLED)"
  type        = string
  default     = "false"
}

# ----------------------------
# Password Policy
# ----------------------------
variable "password_require_uppercase" {
  description = "Require uppercase characters in passwords (PASSWORD_REQUIRE_UPPERCASE)"
  type        = string
  default     = "false"
}

variable "password_require_lowercase" {
  description = "Require lowercase characters in passwords (PASSWORD_REQUIRE_LOWERCASE)"
  type        = string
  default     = "false"
}

variable "password_require_special" {
  description = "Require special characters in passwords (PASSWORD_REQUIRE_SPECIAL)"
  type        = string
  default     = "false"
}

# ----------------------------
# Timeouts / Intervals
# ----------------------------
variable "mcpgateway_ui_tool_test_timeout" {
  description = "Timeout in ms for tool test calls from the UI (MCPGATEWAY_UI_TOOL_TEST_TIMEOUT)"
  type        = number
  default     = 120000
}

variable "health_check_interval" {
  description = "Interval in seconds between gateway health checks (HEALTH_CHECK_INTERVAL)"
  type        = number
  default     = 300
}

variable "global_config_cache_ttl" {
  description = "TTL in seconds for the global configuration cache (GLOBAL_CONFIG_CACHE_TTL)"
  type        = number
  default     = 300
}

# ----------------------------
# Logging
# ----------------------------
variable "log_file" {
  description = "Log file name (LOG_FILE)"
  type        = string
  default     = "mcpgateway.log"
}

variable "log_folder" {
  description = "Directory where log files are written (LOG_FOLDER)"
  type        = string
  default     = "logs"
}

# ----------------------------
# OpenTelemetry
# ----------------------------
variable "otel_exporter_otlp_endpoint" {
  description = "OTLP collector endpoint for OpenTelemetry traces (OTEL_EXPORTER_OTLP_ENDPOINT)"
  type        = string
  default     = ""
}

# ----------------------------
# MCP Client
# ----------------------------
variable "mcp_client_auth_enabled" {
  description = "Enable authentication for MCP client connections (MCP_CLIENT_AUTH_ENABLED)"
  type        = string
  default     = "true"
}

# ----------------------------
# Plugins
# ----------------------------
variable "plugins_enabled" {
  description = "Enable the plugins subsystem (PLUGINS_ENABLED)"
  type        = string
  default     = "true"
}

variable "plugins_config_file" {
  description = "Path to the plugins configuration file (PLUGINS_CONFIG_FILE)"
  type        = string
  default     = "plugins/config_demo.yaml"
}

variable "plugins_log_level" {
  description = "Log level for plugin execution (PLUGINS_LOG_LEVEL)"
  type        = string
  default     = "INFO"
}

variable "plugins_cli_markup_mode" {
  description = "CLI markup rendering mode for plugins (PLUGINS_CLI_MARKUP_MODE)"
  type        = string
  default     = "rich"
}
