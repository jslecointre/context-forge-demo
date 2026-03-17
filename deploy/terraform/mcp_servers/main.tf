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
  name       = "icr-secret"
  project_id = local.project_id
  format     = "registry"
  data = {
    username = "iamapikey"
    password = var.ibmcloud_api_key
    server   = var.cr_registry_server
  }
}

# ----------------------------
# App 1 – Underwriting MCP Server (port 8007)
# Entry point: uv run underwriting_mcp_server.py
# Needs Watsonx credentials for vector search
# ----------------------------
resource "ibm_code_engine_app" "underwriting_mcp" {
  name                = var.mcp_server1_name
  project_id          = local.project_id
  image_reference     = local.image_ref
  image_secret        = ibm_code_engine_secret.registry_secret.name
  scale_min_instances = 1
  scale_cpu_limit     = "8"
  scale_memory_limit  = "16G"
  image_port          = var.mcp_server1_port
  run_commands        = ["uv", "run", var.mcp_server1_script]

  run_env_variables {
    name  = "MCP_PORT"
    value = tostring(var.mcp_server1_port)
    type  = "literal"
  }
  run_env_variables {
    name  = "MCP_TRANSPORT"
    value = var.mcp_transport
    type  = "literal"
  }
  run_env_variables {
    name  = "WATSONX_APIKEY"
    value = var.watson_ai_api_key
    type  = "literal"
  }
  run_env_variables {
    name  = "WATSONX_URL"
    value = var.ibm_cloud_url
    type  = "literal"
  }
  run_env_variables {
    name  = "WATSONX_PROJECT_ID"
    value = var.watson_ai_project_id
    type  = "literal"
  }
}

# ----------------------------
# App 2 – CRM MCP Server (port 8010)
# Entry point: uv run crm_mcp_server.py
# ----------------------------
resource "ibm_code_engine_app" "crm_mcp" {
  name                = var.mcp_server2_name
  project_id          = local.project_id
  image_reference     = local.image_ref
  image_secret        = ibm_code_engine_secret.registry_secret.name
  scale_min_instances = 1
  scale_cpu_limit     = "8"
  scale_memory_limit  = "16G"
  image_port          = var.mcp_server2_port
  run_commands        = ["uv", "run", var.mcp_server2_script]

  run_env_variables {
    name  = "MCP_PORT"
    value = tostring(var.mcp_server2_port)
    type  = "literal"
  }
  run_env_variables {
    name  = "MCP_TRANSPORT"
    value = var.mcp_transport
    type  = "literal"
  }
}

# ----------------------------
# App 3 – Health MCP Server (port 8009)
# Entry point: uv run health_mcp_server.py
# ----------------------------
resource "ibm_code_engine_app" "health_mcp" {
  name                = var.mcp_server3_name
  project_id          = local.project_id
  image_reference     = local.image_ref
  image_secret        = ibm_code_engine_secret.registry_secret.name
  scale_min_instances = 1
  scale_cpu_limit     = "8"
  scale_memory_limit  = "16G"
  image_port          = var.mcp_server3_port
  run_commands        = ["uv", "run", var.mcp_server3_script]

  run_env_variables {
    name  = "MCP_PORT"
    value = tostring(var.mcp_server3_port)
    type  = "literal"
  }
  run_env_variables {
    name  = "MCP_TRANSPORT"
    value = var.mcp_transport
    type  = "literal"
  }
}

# ----------------------------
# Outputs
# ----------------------------
output "underwriting_mcp_endpoint" {
  value = ibm_code_engine_app.underwriting_mcp.endpoint
}

output "crm_mcp_endpoint" {
  value = ibm_code_engine_app.crm_mcp.endpoint
}

output "health_mcp_endpoint" {
  value = ibm_code_engine_app.health_mcp.endpoint
}
