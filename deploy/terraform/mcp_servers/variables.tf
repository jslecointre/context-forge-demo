# ----------------------------
# Variables
# ----------------------------
variable "ibmcloud_api_key" {
  type        = string
  default     = ""
  description = "IBM Cloud API Key"
  sensitive   = true
}

variable "watson_ai_api_key" {
  type        = string
  default     = ""
  description = "Watsonx AI API Key"
  sensitive   = true
}

variable "ibm_cloud_url" {
  description = "Watsonx.ai service URL (WATSONX_URL)"
  default     = "https://us-south.ml.cloud.ibm.com"
}

variable "watson_ai_project_id" {
  type        = string
  description = "watsonx.ai project id. Open the project, go to Management->General->Details"
  default     = ""
  sensitive   = true
}

variable "region" {
  description = "Region where Code Engine project exists"
  type        = string
  default     = "us-south"
}

variable "image_name" {
  description = "Base MCP image name (used by crm and health servers)"
  type        = string
  default     = "mcp-server"
}

variable "cr_registry_server" {
  description = "Container Registry server hostname."
  type        = string
  default     = "us.icr.io"
}

variable "cr_namespace" {
  description = "Container Registry namespace where the MCP image is stored"
  type        = string
  default     = "<your-cr-namespace>"
}

variable "mcp_transport" {
  description = "MCP transport protocol used by all servers (sse, streamable-http, stdio)"
  type        = string
  default     = "mcp"
}

# ----------------------------
# MCP Server 1 - Underwriting
# ----------------------------
variable "mcp_server1_name" {
  description = "Code Engine app name for the underwriting MCP server"
  type        = string
  default     = "underwriting-mcp-server"
}

variable "mcp_server1_port" {
  description = "Listening port for the underwriting MCP server"
  type        = number
  default     = 8007
}

variable "mcp_server1_script" {
  description = "Entry-point script for the underwriting MCP server"
  type        = string
  default     = "underwriting_mcp_server.py"
}

# ----------------------------
# MCP Server 2 - CRM
# ----------------------------
variable "mcp_server2_name" {
  description = "Code Engine app name for the CRM MCP server"
  type        = string
  default     = "crm-mcp-server"
}

variable "mcp_server2_port" {
  description = "Listening port for the CRM MCP server"
  type        = number
  default     = 8010
}

variable "mcp_server2_script" {
  description = "Entry-point script for the CRM MCP server"
  type        = string
  default     = "crm_mcp_server.py"
}

# ----------------------------
# MCP Server 3 - Health
# ----------------------------
variable "mcp_server3_name" {
  description = "Code Engine app name for the health MCP server"
  type        = string
  default     = "health-mcp-server"
}

variable "mcp_server3_port" {
  description = "Listening port for the health MCP server"
  type        = number
  default     = 8009
}

variable "mcp_server3_script" {
  description = "Entry-point script for the health MCP server"
  type        = string
  default     = "health_mcp_server.py"
}

variable "ce_project_name" {
  description = "Code Engine project name. Overrides the auto-derived 'ce-<resource_group>' name when set."
  type        = string
  default     = ""
}
