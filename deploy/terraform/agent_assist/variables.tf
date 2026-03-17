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
  description = "Container Registry namespace where the agent-assist image is stored"
  type        = string
  default     = ""
}

variable "image_name" {
  description = "Agent-assist image name in the Container Registry"
  type        = string
  default     = "agent-assist-app"
}

# ----------------------------
# Agent-Assist App
# ----------------------------
variable "app_name" {
  description = "Code Engine app name for the agent-assist service"
  type        = string
  default     = "agent-assist-app"
}

variable "app_port" {
  description = "Listening port for the agent-assist app"
  type        = number
  default     = 8002
}

variable "backend_url" {
  description = "Public URL of this app (Code Engine endpoint). Used by the frontend to reach the backend API. Set after first deploy if not yet known."
  type        = string
  default     = ""
}

variable "backend_auth" {
  description = "Enable HTTP Basic Auth on the backend API (true | false)"
  type        = string
  default     = "false"
}

variable "backend_user" {
  description = "HTTP Basic Auth username for the backend API"
  type        = string
  default     = "user"
}

variable "backend_password" {
  description = "HTTP Basic Auth password for the backend API"
  type        = string
  default     = "password"
  sensitive   = true
}

# ----------------------------
# Watsonx.ai
# ----------------------------
variable "watsonx_apikey" {
  type        = string
  description = "Watsonx AI API Key"
  default     = ""
  sensitive   = true
}

variable "watsonx_url" {
  description = "Watsonx.ai service URL"
  type        = string
  default     = "https://us-south.ml.cloud.ibm.com"
}

variable "watsonx_project_id" {
  type        = string
  description = "Watsonx.ai project ID"
  default     = ""
  sensitive   = true
}

# ----------------------------
# OpenAI
# ----------------------------
variable "openai_api_key" {
  type        = string
  description = "OpenAI API Key"
  default     = ""
  sensitive   = true
}

# ----------------------------
# Model
# ----------------------------
variable "model" {
  description = "LLM model identifier used by the agent-assist app"
  type        = string
  default     = ""
}

# ----------------------------
# LangSmith
# ----------------------------
variable "langsmith_api_key" {
  type        = string
  description = "LangSmith API Key"
  default     = ""
  sensitive   = true
}

variable "langsmith_tracing" {
  type        = string
  description = "Enable LangSmith tracing (true | false)"
  default     = "false"
}

variable "langsmith_project" {
  type        = string
  description = "LangSmith project name"
  default     = ""
}

# ----------------------------
# Langfuse
# ----------------------------
variable "langfuse_base_url" {
  description = "Langfuse base URL for tracing"
  type        = string
  default     = ""
}

variable "langfuse_secret_key" {
  type        = string
  description = "Langfuse secret key"
  default     = ""
  sensitive   = true
}

variable "langfuse_public_key" {
  type        = string
  description = "Langfuse public key"
  default     = ""
}

# ----------------------------
# MCP Servers – Hosts (IBM Code Engine endpoints)
# ----------------------------
variable "mcp_host1" {
  description = "Full URL of the underwriting MCP server (e.g. IBM Code Engine endpoint)"
  type        = string
  default     = ""
}

variable "mcp_host2" {
  description = "Full URL of the CRM MCP server (e.g. IBM Code Engine endpoint)"
  type        = string
  default     = ""
}

variable "mcp_host3" {
  description = "Full URL of the health MCP server (e.g. IBM Code Engine endpoint)"
  type        = string
  default     = ""
}

# ----------------------------
# MCP Servers – Ports
# ----------------------------
variable "mcp_port1" {
  description = "Port for the underwriting MCP server"
  type        = number
  default     = 8007
}

variable "mcp_port2" {
  description = "Port for the CRM MCP server"
  type        = number
  default     = 8008
}

variable "mcp_port3" {
  description = "Port for the health MCP server"
  type        = number
  default     = 8009
}

# ----------------------------
# MCP Servers – Transport
# ----------------------------
variable "mcp_transport1" {
  description = "MCP transport protocol for server 1 (sse | streamable-http | mcp)"
  type        = string
  default     = "mcp"
}

variable "mcp_transport2" {
  description = "MCP transport protocol for server 2 (sse | streamable-http | mcp)"
  type        = string
  default     = "mcp"
}

variable "mcp_transport3" {
  description = "MCP transport protocol for server 3 (sse | streamable-http | mcp)"
  type        = string
  default     = "mcp"
}

# ----------------------------
# Context Forge
# ----------------------------
variable "context_forge_base_url" {
  description = "Base URL of the Context Forge / MCP gateway service"
  type        = string
  default     = ""
}

variable "context_forge_mcp_transport" {
  description = "MCP transport used to connect to Context Forge"
  type        = string
  default     = "mcp"
}

variable "context_forge_admin_username" {
  type        = string
  description = "Context Forge admin username"
  default     = ""
}

variable "context_forge_admin_password" {
  type        = string
  description = "Context Forge admin password"
  default     = ""
  sensitive   = true
}

variable "broker_context_forge_token" {
  type        = string
  description = "Context Forge token for the broker persona"
  default     = ""
  sensitive   = true
}

variable "analyst_context_forge_token" {
  type        = string
  description = "Context Forge token for the analyst persona"
  default     = ""
  sensitive   = true
}

variable "broker_context_forge_vserver" {
  type        = string
  description = "Context Forge virtual server name for the broker persona"
  default     = ""
}

variable "analyst_context_forge_vserver" {
  type        = string
  description = "Context Forge virtual server name for the analyst persona"
  default     = ""
}
