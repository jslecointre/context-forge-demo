locals {
  project_id = data.external.project_search.result.project_id
  image_ref  = format("%s/%s/%s:0.0.0", var.cr_registry_server, var.cr_namespace, var.image_name)
}


data "ibm_iam_auth_token" "tokendata" {}


data "external" "project_search" {
  program = ["bash", "${path.module}/../../scripts/fetchProjectID.sh", var.ce_project_name, data.ibm_iam_auth_token.tokendata.iam_access_token, var.region]
}

# ----------------------------
# Registry Secret
# ----------------------------
resource "ibm_code_engine_secret" "registry_secret" {
  name       = "icr-secret-agent-assist"
  project_id = local.project_id
  format     = "registry"
  data = {
    username = "iamapikey"
    password = var.ibmcloud_api_key
    server   = var.cr_registry_server
  }
}

# ----------------------------
# Agent-Assist App (port 8002)
# ----------------------------
resource "ibm_code_engine_app" "agent_assist" {
  name                = var.app_name
  project_id          = local.project_id
  image_reference     = local.image_ref
  image_secret        = ibm_code_engine_secret.registry_secret.name
  scale_min_instances = 1
  scale_cpu_limit     = "4"
  scale_memory_limit  = "8G"
  image_port          = var.app_port

  # --- Backend ---
  run_env_variables {
    name  = "BACKEND_URL"
    value = var.backend_url
    type  = "literal"
  }
  run_env_variables {
    name  = "BACKEND_AUTH"
    value = var.backend_auth
    type  = "literal"
  }
  run_env_variables {
    name  = "BACKEND_USER"
    value = var.backend_user
    type  = "literal"
  }
  run_env_variables {
    name  = "BACKEND_PASSWORD"
    value = var.backend_password
    type  = "literal"
  }

  # --- Watsonx.ai ---
  run_env_variables {
    name  = "WATSONX_APIKEY"
    value = var.watsonx_apikey
    type  = "literal"
  }
  run_env_variables {
    name  = "WATSONX_URL"
    value = var.watsonx_url
    type  = "literal"
  }
  run_env_variables {
    name  = "WATSONX_PROJECT_ID"
    value = var.watsonx_project_id
    type  = "literal"
  }

  # --- OpenAI ---
  run_env_variables {
    name  = "OPENAI_API_KEY"
    value = var.openai_api_key
    type  = "literal"
  }

  # --- Model ---
  run_env_variables {
    name  = "MODEL"
    value = var.model
    type  = "literal"
  }

  # --- LangSmith ---
  run_env_variables {
    name  = "LANGSMITH_API_KEY"
    value = var.langsmith_api_key
    type  = "literal"
  }
  run_env_variables {
    name  = "LANGSMITH_TRACING"
    value = var.langsmith_tracing
    type  = "literal"
  }
  run_env_variables {
    name  = "LANGSMITH_PROJECT"
    value = var.langsmith_project
    type  = "literal"
  }

  # --- Langfuse ---
  run_env_variables {
    name  = "LANGFUSE_BASE_URL"
    value = var.langfuse_base_url
    type  = "literal"
  }
  run_env_variables {
    name  = "LANGFUSE_SECRET_KEY"
    value = var.langfuse_secret_key
    type  = "literal"
  }
  run_env_variables {
    name  = "LANGFUSE_PUBLIC_KEY"
    value = var.langfuse_public_key
    type  = "literal"
  }

  # --- MCP Server Hosts ---
  run_env_variables {
    name  = "MCP_HOST1"
    value = var.mcp_host1
    type  = "literal"
  }
  run_env_variables {
    name  = "MCP_HOST2"
    value = var.mcp_host2
    type  = "literal"
  }
  run_env_variables {
    name  = "MCP_HOST3"
    value = var.mcp_host3
    type  = "literal"
  }

  # --- MCP Server Ports ---
  run_env_variables {
    name  = "MCP_PORT1"
    value = tostring(var.mcp_port1)
    type  = "literal"
  }
  run_env_variables {
    name  = "MCP_PORT2"
    value = tostring(var.mcp_port2)
    type  = "literal"
  }
  run_env_variables {
    name  = "MCP_PORT3"
    value = tostring(var.mcp_port3)
    type  = "literal"
  }

  # --- MCP Server Transports ---
  run_env_variables {
    name  = "MCP_TRANSPORT1"
    value = var.mcp_transport1
    type  = "literal"
  }
  run_env_variables {
    name  = "MCP_TRANSPORT2"
    value = var.mcp_transport2
    type  = "literal"
  }
  run_env_variables {
    name  = "MCP_TRANSPORT3"
    value = var.mcp_transport3
    type  = "literal"
  }

  # --- Context Forge ---
  run_env_variables {
    name  = "CONTEXT_FORGE_BASE_URL"
    value = var.context_forge_base_url
    type  = "literal"
  }
  run_env_variables {
    name  = "CONTEXT_FORGE_MCP_TRANSPORT"
    value = var.context_forge_mcp_transport
    type  = "literal"
  }
  run_env_variables {
    name  = "CONTEXT_FORGE_ADMIN_USERNAME"
    value = var.context_forge_admin_username
    type  = "literal"
  }
  run_env_variables {
    name  = "CONTEXT_FORGE_ADMIN_PASSWORD"
    value = var.context_forge_admin_password
    type  = "literal"
  }
  run_env_variables {
    name  = "BROKER_CONTEXT_FORGE_TOKEN"
    value = var.broker_context_forge_token
    type  = "literal"
  }
  run_env_variables {
    name  = "ANALYST_CONTEXT_FORGE_TOKEN"
    value = var.analyst_context_forge_token
    type  = "literal"
  }
  run_env_variables {
    name  = "BROKER_CONTEXT_FORGE_VSERVER"
    value = var.broker_context_forge_vserver
    type  = "literal"
  }
  run_env_variables {
    name  = "ANALYST_CONTEXT_FORGE_VSERVER"
    value = var.analyst_context_forge_vserver
    type  = "literal"
  }
}

# ----------------------------
# Outputs
# ----------------------------
output "agent_assist_endpoint" {
  value = ibm_code_engine_app.agent_assist.endpoint
}
