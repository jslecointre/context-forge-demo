locals {
  project_id = data.external.project_search.result.project_id
  image_ref  = format("%s/%s/%s:0.0.0", var.cr_registry_server, var.cr_namespace, var.image_name)
  redis_url  = var.redis_url != "" ? var.redis_url : "redis://${var.redis_app_name}:6379"
}


data "ibm_iam_auth_token" "tokendata" {}


data "external" "project_search" {
  program = ["bash", "${path.module}/../../scripts/fetchProjectID.sh", var.ce_project_name, data.ibm_iam_auth_token.tokendata.iam_access_token, var.region]
}

# ----------------------------
# Registry Secret (mcp-context-forge-plugin image)
# ----------------------------
resource "ibm_code_engine_secret" "registry_secret" {
  name       = "icr-secret-context-forge"
  project_id = local.project_id
  format     = "registry"
  data = {
    username = "iamapikey"
    password = var.ibmcloud_api_key
    server   = var.cr_registry_server
  }
}

# ----------------------------
# Redis App
# For production, replace with IBM Databases for Redis and set var.redis_url.
# ----------------------------
resource "ibm_code_engine_app" "redis" {
  name                = var.redis_app_name
  project_id          = local.project_id
  image_reference     = "redis:7-alpine"
  scale_min_instances = 1
  scale_cpu_limit     = "0.5"
  scale_memory_limit  = "1G"
  image_port          = 6379
  run_commands        = ["redis-server"]
  run_arguments       = ["--appendonly", "yes"]
}

# ----------------------------
# MCP Context Forge Plugin App (port 4444)
# ----------------------------
resource "ibm_code_engine_app" "mcp_context_forge" {
  name                = var.app_name
  project_id          = local.project_id
  image_reference     = local.image_ref
  image_secret        = ibm_code_engine_secret.registry_secret.name
  scale_min_instances = 1
  scale_cpu_limit     = "1"
  scale_memory_limit  = "2G"
  image_port          = var.app_port

  # --- Redis (overrides any value from .env.contextforge, mirrors docker-compose override) ---
  run_env_variables {
    name  = "REDIS_URL"
    value = local.redis_url
    type  = "literal"
  }

  # --- Authentication ---
  run_env_variables {
    name  = "BASIC_AUTH_USER"
    value = var.basic_auth_user
    type  = "literal"
  }
  run_env_variables {
    name  = "BASIC_AUTH_PASSWORD"
    value = var.basic_auth_password
    type  = "literal"
  }
  run_env_variables {
    name  = "JWT_SECRET_KEY"
    value = var.jwt_secret_key
    type  = "literal"
  }
  run_env_variables {
    name  = "AUTH_ENCRYPTION_SECRET"
    value = var.auth_encryption_secret
    type  = "literal"
  }

  # --- Platform Admin ---
  run_env_variables {
    name  = "PLATFORM_ADMIN_EMAIL"
    value = var.platform_admin_email
    type  = "literal"
  }
  run_env_variables {
    name  = "PLATFORM_ADMIN_PASSWORD"
    value = var.platform_admin_password
    type  = "literal"
  }
  run_env_variables {
    name  = "DEFAULT_USER_PASSWORD"
    value = var.default_user_password
    type  = "literal"
  }

  # --- Token Settings ---
  run_env_variables {
    name  = "REQUIRE_JTI"
    value = var.require_jti
    type  = "literal"
  }
  run_env_variables {
    name  = "REQUIRE_TOKEN_EXPIRATION"
    value = var.require_token_expiration
    type  = "literal"
  }
  run_env_variables {
    name  = "PUBLIC_REGISTRATION_ENABLED"
    value = var.public_registration_enabled
    type  = "literal"
  }
  run_env_variables {
    name  = "ALLOW_PUBLIC_VISIBILITY"
    value = var.allow_public_visibility
    type  = "literal"
  }

  # --- Network ---
  run_env_variables {
    name  = "HOST"
    value = var.host
    type  = "literal"
  }
  run_env_variables {
    name  = "APP_DOMAIN"
    value = var.app_domain
    type  = "literal"
  }

  # --- Gateway Features ---
  run_env_variables {
    name  = "MCPGATEWAY_UI_ENABLED"
    value = var.mcpgateway_ui_enabled
    type  = "literal"
  }
  run_env_variables {
    name  = "MCPGATEWAY_ADMIN_API_ENABLED"
    value = var.mcpgateway_admin_api_enabled
    type  = "literal"
  }
  run_env_variables {
    name  = "MCPGATEWAY_WS_RELAY_ENABLED"
    value = var.mcpgateway_ws_relay_enabled
    type  = "literal"
  }
  run_env_variables {
    name  = "MCPGATEWAY_REVERSE_PROXY_ENABLED"
    value = var.mcpgateway_reverse_proxy_enabled
    type  = "literal"
  }

  # --- SSRF Protection ---
  run_env_variables {
    name  = "SSRF_ALLOW_LOCALHOST"
    value = var.ssrf_allow_localhost
    type  = "literal"
  }
  run_env_variables {
    name  = "SSRF_ALLOW_PRIVATE_NETWORKS"
    value = var.ssrf_allow_private_networks
    type  = "literal"
  }
  run_env_variables {
    name  = "SSRF_DNS_FAIL_CLOSED"
    value = var.ssrf_dns_fail_closed
    type  = "literal"
  }

  # --- Security ---
  run_env_variables {
    name  = "SECURE_COOKIES"
    value = var.secure_cookies
    type  = "literal"
  }
  run_env_variables {
    name  = "DANGEROUS_PATTERNS"
    value = jsonencode(var.dangerous_patterns)
    type  = "literal"
  }

  # --- Validation / Audit ---
  run_env_variables {
    name  = "EXPERIMENTAL_VALIDATE_IO"
    value = var.experimental_validate_io
    type  = "literal"
  }
  run_env_variables {
    name  = "VALIDATION_MIDDLEWARE_ENABLED"
    value = var.validation_middleware_enabled
    type  = "literal"
  }
  run_env_variables {
    name  = "PERMISSION_AUDIT_ENABLED"
    value = var.permission_audit_enabled
    type  = "literal"
  }

  # --- Password Policy ---
  run_env_variables {
    name  = "PASSWORD_REQUIRE_UPPERCASE"
    value = var.password_require_uppercase
    type  = "literal"
  }
  run_env_variables {
    name  = "PASSWORD_REQUIRE_LOWERCASE"
    value = var.password_require_lowercase
    type  = "literal"
  }
  run_env_variables {
    name  = "PASSWORD_REQUIRE_SPECIAL"
    value = var.password_require_special
    type  = "literal"
  }

  # --- Timeouts / Intervals ---
  run_env_variables {
    name  = "MCPGATEWAY_UI_TOOL_TEST_TIMEOUT"
    value = tostring(var.mcpgateway_ui_tool_test_timeout)
    type  = "literal"
  }
  run_env_variables {
    name  = "HEALTH_CHECK_INTERVAL"
    value = tostring(var.health_check_interval)
    type  = "literal"
  }
  run_env_variables {
    name  = "GLOBAL_CONFIG_CACHE_TTL"
    value = tostring(var.global_config_cache_ttl)
    type  = "literal"
  }

  # --- Logging ---
  run_env_variables {
    name  = "LOG_FILE"
    value = var.log_file
    type  = "literal"
  }
  run_env_variables {
    name  = "LOG_FOLDER"
    value = var.log_folder
    type  = "literal"
  }

  # --- OpenTelemetry ---
  run_env_variables {
    name  = "OTEL_EXPORTER_OTLP_ENDPOINT"
    value = var.otel_exporter_otlp_endpoint
    type  = "literal"
  }

  # --- MCP Client ---
  run_env_variables {
    name  = "MCP_CLIENT_AUTH_ENABLED"
    value = var.mcp_client_auth_enabled
    type  = "literal"
  }

  # --- Plugins ---
  run_env_variables {
    name  = "PLUGINS_ENABLED"
    value = var.plugins_enabled
    type  = "literal"
  }
  run_env_variables {
    name  = "PLUGINS_CONFIG_FILE"
    value = var.plugins_config_file
    type  = "literal"
  }
  run_env_variables {
    name  = "PLUGINS_LOG_LEVEL"
    value = var.plugins_log_level
    type  = "literal"
  }
  run_env_variables {
    name  = "PLUGINS_CLI_MARKUP_MODE"
    value = var.plugins_cli_markup_mode
    type  = "literal"
  }

  depends_on = [ibm_code_engine_app.redis]
}

# ----------------------------
# Outputs
# ----------------------------
output "context_forge_endpoint" {
  description = "Public Code Engine endpoint for mcp-context-forge-plugin"
  value       = ibm_code_engine_app.mcp_context_forge.endpoint
}

output "redis_endpoint" {
  description = "Code Engine endpoint for the Redis service"
  value       = ibm_code_engine_app.redis.endpoint
}
