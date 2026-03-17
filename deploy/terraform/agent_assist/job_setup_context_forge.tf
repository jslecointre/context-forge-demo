# ----------------------------
# Setup Context Forge – Job
# ----------------------------
# One-shot provisioning job: registers teams, gateways and virtual servers
# in the mcp-context-forge-plugin service.
#
# The job uses the same image as agent-assist-app but overrides the command
# to run setup_context_forge.py. It only needs Context Forge + MCP env vars.
#
# TRIGGERING
#   Option A (manual – after terraform apply):
#     ibmcloud ce project select --name <project>
#     ibmcloud ce jobrun submit --job setup-context-forge --wait
#
#   Option B (automatic on terraform apply):
#     Uncomment the null_resource block below.
#     Requires: ibmcloud CLI logged in on the machine running terraform.
# ----------------------------

resource "ibm_code_engine_job" "setup_context_forge" {
  name            = "setup-context-forge"
  project_id      = local.project_id
  image_reference = local.image_ref
  image_secret    = ibm_code_engine_secret.registry_secret.name

  run_commands  = ["python"]
  run_arguments = ["/app/backend/setup_context_forge.py"]

  # Retry up to 5 times so transient startup delays of Context Forge
  # are handled by Code Engine rather than a manual re-submit.
  scale_retry_limit = 5
  scale_cpu_limit   = "1"
  scale_memory_limit = "2G"

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
}

# ----------------------------
# Option B: auto-trigger on apply
# Uncomment to submit a job run automatically after the job definition is created.
# Requires the ibmcloud CLI to be authenticated in the shell running terraform.
# ----------------------------
# resource "null_resource" "trigger_setup_context_forge" {
#   depends_on = [ibm_code_engine_job.setup_context_forge]
#
#   provisioner "local-exec" {
#     command = <<-EOT
#       ibmcloud ce project select --name ${local.project_name} --quiet
#       ibmcloud ce jobrun submit --job ${ibm_code_engine_job.setup_context_forge.name} --wait
#     EOT
#   }
#
#   # Re-run whenever the job definition changes (image or env vars).
#   triggers = {
#     job_image = ibm_code_engine_job.setup_context_forge.image_reference
#   }
# }

# ----------------------------
# Outputs
# ----------------------------
output "setup_context_forge_job_name" {
  value = ibm_code_engine_job.setup_context_forge.name
}
