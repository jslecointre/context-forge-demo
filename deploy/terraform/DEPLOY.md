# Deployment Guide — Context Forge Demo on IBM Code Engine

This guide walks you through deploying the Context Forge Demo to IBM Code Engine using Terraform, from building and pushing container images to running the full agentic insurance workflow with role-based access control.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Build and Push All Container Images](#2-build-and-push-all-container-images)
3. [Deploy the MCP Servers](#3-deploy-the-mcp-servers)
4. [Deploy the MCP Gateway (Context Forge)](#4-deploy-the-mcp-gateway-context-forge)
5. [Populate Agent Assist Variables](#5-populate-agent-assist-variables)
6. [Deploy the Agent Assist Application](#6-deploy-the-agent-assist-application)
7. [Run the Setup Job](#7-run-the-setup-job)
8. [Create Team Tokens](#8-create-team-tokens)
9. [Update Agent Assist Environment Variables](#9-update-agent-assist-environment-variables)
10. [Test the Application](#10-test-the-application)
11. [Check Application Logs](#11-check-application-logs)

---

## 1. Prerequisites

Before you begin, make sure the following are installed and available:

| Requirement | Notes |
|---|---|
| [Terraform](https://developer.hashicorp.com/terraform/install) ≥ 1.5 | Used for all deployments |
| [IBM Cloud CLI](https://cloud.ibm.com/docs/cli) + `ibmcloud ce` plugin | Required to trigger Code Engine job runs |
| Docker | Required to build and push images |
| `make` | Available by default on macOS/Linux |
| IBM Cloud API Key | Must have access to Code Engine and Container Registry |
| IBM WatsonX credentials | `WATSONX_APIKEY` and `WATSONX_PROJECT_ID` |

Log in to IBM Cloud before running any Terraform or CLI commands.

**With an API key:**

```bash
ibmcloud login --apikey <IBMCLOUD_API_KEY> -r us-south
ibmcloud cr login
```

**With SSO (browser-based):**

```bash
ibmcloud login --sso -a https://cloud.ibm.com -r us-south
ibmcloud cr login
```

Then select your Code Engine project:

```bash
ibmcloud ce project select --name your-ce-project-name
```

---

## 2. Build and Push All Container Images

Build and push all three container images to your IBM Container Registry namespace. All images must be available before Terraform can deploy them.

### MCP Server image

The `mcp-server` image powers all three MCP servers (underwriting, CRM, health). The build step also ingests the PDF manuals into Chroma so they are embedded in the image.

```bash
# Build (downloads PDFs and runs ingestion)
make build-mcp-server

# Push to registry
make push
```

### Context Forge Plugin image

```bash
make build-context-forge-plugin

docker push <REPOSITORY>/mcp-context-forge-plugin:0.0.0
```

### Agent Assist image

```bash
# Build the shared Python base layer first
make build-base

# Build the agent-assist application image
make build-agent-assist

# Push to registry
make push-agent-assist-app
```

> Set `REPOSITORY` to your Container Registry namespace, e.g.:
> ```bash
> export REPOSITORY=us.icr.io/your-namespace
> ```
> All three images must be tagged `0.0.0` (the default `VERSION`).

---

## 3. Deploy the MCP Servers

The `mcp_servers` Terraform module deploys three Code Engine applications: `underwriting-mcp-server`, `crm-mcp-server`, and `health-mcp-server`.

### Configure variables

```bash
cd deploy/terraform/mcp_servers
cp terraform.tfvars.example terraform.tfvars
```

> **Multiple environments:** If you need to deploy to several environments (e.g. dev, staging, prod), create one `.tfvars` file per environment and pass it explicitly at apply time:
> ```bash
> cp terraform.tfvars.example terraform.dev.tfvars
> cp terraform.tfvars.example terraform.prod.tfvars
> ```
> Then target the right one with `-var-file` (see the Apply step below).

Edit `terraform.tfvars` and set at minimum:

```hcl
ibmcloud_api_key     = "<your-ibmcloud-api-key>"
region               = "us-south"

cr_registry_server   = "us.icr.io"
cr_namespace         = "<your-cr-namespace>"
image_name           = "mcp-server"

ce_project_name      = "your-ce-project-name"          # your Code Engine project

# Watsonx.ai — required by the underwriting server
ibm_cloud_url        = "https://us-south.ml.cloud.ibm.com"
watson_ai_project_id = "<your-watsonx-project-id>"
watson_ai_api_key    = "<your-watsonx-api-key>"
```

### Apply

```bash
terraform init
terraform apply -var-file="terraform.tfvars"

# For a named environment file:
# terraform apply -var-file="terraform.prod.tfvars"
```

### Record the MCP server URLs

After `terraform apply` completes, copy the three endpoint URLs from the outputs:

```
Outputs:

underwriting_mcp_endpoint = "https://underwriting-mcp-server.<hash>.us-south.codeengine.appdomain.cloud"
crm_mcp_endpoint          = "https://crm-mcp-server.<hash>.us-south.codeengine.appdomain.cloud"
health_mcp_endpoint       = "https://health-mcp-server.<hash>.us-south.codeengine.appdomain.cloud"
```

You will need these three URLs in [Step 5](#5-populate-agent-assist-variables).

> **Underwriting server**: The PDF manuals are ingested into Chroma during `make build-mcp-server` and baked into the image. The server is ready as soon as the container starts.

---

## 4. Deploy the MCP Gateway (Context Forge)

The `context_forge` module deploys a Redis instance and the `mcp-context-forge-plugin` gateway to Code Engine.

### Configure variables

```bash
cd ../context_forge
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and set at minimum:

```hcl
ibmcloud_api_key = "<your-ibmcloud-api-key>"
region           = "us-south"

ce_project_name  = "your-ce-project-name"

cr_registry_server = "us.icr.io"
cr_namespace       = "<your-cr-namespace>"
image_name         = "mcp-context-forge-plugin"

# Authentication — change these from the defaults before deploying
basic_auth_password    = "<strong-password>"
jwt_secret_key         = "<random-secret-key>"
auth_encryption_secret = "<random-encryption-salt>"

platform_admin_email    = "admin@example.com"
platform_admin_password = "<strong-admin-password>"
default_user_password   = "<default-user-password>"

# Leave as http://localhost for the first deploy — update after you get the endpoint
app_domain = "http://localhost"
```

### Apply

```bash
terraform init
terraform apply -var-file="terraform.tfvars"
```

### Record the Context Forge gateway URL

Copy the gateway endpoint from the outputs:

```
Outputs:

context_forge_endpoint = "https://mcp-context-forge-plugin.<hash>.us-south.codeengine.appdomain.cloud"
```

### Update app_domain and re-apply

Once you have the endpoint, update `app_domain` in `terraform.tfvars` to the public URL and re-apply so the gateway knows its own address:

```hcl
app_domain = "https://mcp-context-forge-plugin.<hash>.us-south.codeengine.appdomain.cloud"
```

```bash
terraform apply -var-file="terraform.tfvars"
```

### Log in to the Context Forge Admin UI

Open `https://<context_forge_endpoint>/admin/login` in your browser.

| Field | Value |
|---|---|
| Email | value of `platform_admin_email` |
| Password | value of `platform_admin_password` |

---

## 5. Populate Agent Assist Variables

Before deploying the agent-assist application, fill in all required values in the `agent_assist` terraform variables file. These reference the URLs obtained in previous steps.

```bash
cd ../agent_assist
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:

```hcl
ibmcloud_api_key = "<your-ibmcloud-api-key>"
region           = "us-south"

ce_project_name  = "your-ce-project-name"

cr_registry_server = "us.icr.io"
cr_namespace       = "<your-cr-namespace>"
image_name         = "agent-assist-app"

# Watsonx.ai
watsonx_apikey     = "<your-watsonx-api-key>"
watsonx_url        = "https://us-south.ml.cloud.ibm.com"
watsonx_project_id = "<your-watsonx-project-id>"

# Model
model = "ibm:openai/gpt-oss-120b"

# MCP Server Hosts — paste the outputs from Step 3
mcp_host1 = "https://underwriting-mcp-server.<hash>.us-south.codeengine.appdomain.cloud"
mcp_host2 = "https://crm-mcp-server.<hash>.us-south.codeengine.appdomain.cloud"
mcp_host3 = "https://health-mcp-server.<hash>.us-south.codeengine.appdomain.cloud"

mcp_transport1 = "mcp"
mcp_transport2 = "mcp"
mcp_transport3 = "mcp"

# Context Forge Gateway — paste the output from Step 4
context_forge_base_url       = "https://mcp-context-forge-plugin.<hash>.us-south.codeengine.appdomain.cloud"
context_forge_mcp_transport  = "mcp"
context_forge_admin_username = "admin"
context_forge_admin_password = "<your-context-forge-admin-password>"

# Backend URL — leave empty on first deploy; filled in Step 9 once the endpoint is known
# This URL is injected into the frontend so the browser can reach the API
backend_url  = ""
backend_auth = "false"

# Team tokens and virtual servers — populated in Step 9 after setup job runs
broker_context_forge_token     = ""
analyst_context_forge_token    = ""
broker_context_forge_vserver   = ""
analyst_context_forge_vserver  = ""
```

---

## 6. Deploy the Agent Assist Application

```bash
# still in deploy/terraform/agent_assist
terraform init
terraform apply -var-file="terraform.tfvars"
```

This creates:
- The `agent-assist-app` Code Engine application
- The `setup-context-forge` Code Engine job definition (used in the next step)

Copy the application endpoint from the outputs:

```
Outputs:

agent_assist_endpoint          = "https://agent-assist-app.<hash>.us-south.codeengine.appdomain.cloud"
setup_context_forge_job_name   = "setup-context-forge"
```

---

## 7. Run the Setup Job

The setup job connects to the Context Forge gateway and automatically:

1. Registers the three upstream MCP servers
2. Creates two teams: **Insurance Brokers** and **Insurance Analysts**
3. Provisions one team-scoped virtual server per team with the correct tool subset

### Log in to the Context Forge Admin UI first

Before running the job, confirm the gateway is live by logging in to the Admin UI:

Open `https://<context_forge_endpoint>/admin/login` in your browser and sign in with the `platform_admin_email` / `platform_admin_password` you set in Step 4.

### Option A — IBM Cloud CLI (recommended)

```bash
ibmcloud ce project select --name your-ce-project-name

ibmcloud ce jobrun submit --job setup-context-forge --wait
```

Expected output:

```
Getting jobrun 'setup-context-forge-jobrun-<id>'...
Getting instances of jobrun 'setup-context-forge-jobrun-<id>'...
Getting events of jobrun 'setup-context-forge-jobrun-<id>'...
For troubleshooting information visit: https://cloud.ibm.com/docs/codeengine?topic=codeengine-troubleshoot-job.
Run 'ibmcloud ce jobrun events -n setup-context-forge-jobrun-<id>' to get the system events of the job run instances.
Run 'ibmcloud ce jobrun logs -f -n setup-context-forge-jobrun-<id>' to follow the logs of the job run instances.
```

### Check the job logs and retrieve virtual server IDs

Once the job run name is known, stream the logs to confirm success and capture the virtual server IDs:

```bash
ibmcloud ce jobrun logs -f -n setup-context-forge-jobrun-<id>
```

The log output summarises the full setup in four steps:

| Step | What happens |
|---|---|
| **Step 1** — Health & Auth check | Verifies the gateway is reachable and the admin token is valid |
| **Step 2** — Teams provisioned | Creates **Insurance Brokers** and **Insurance Analysts** teams |
| **Step 3** — Public MCP gateways registered | Registers `underwriting`, `crm`, and `health` upstream servers |
| **Step 4** — Virtual servers created | Provisions `broker_gateway` (4 tools) and `analysts_gateway` (4 tools), each scoped to their team |

At the end of the log the job prints the virtual server IDs and the environment variables you need for the next steps:

```
BROKER_CONTEXT_FORGE_VSERVER=<broker-virtual-server-id>
BROKER_CONTEXT_FORGE_TOKEN=<create a token for the Insurance Brokers team>

ANALYST_CONTEXT_FORGE_VSERVER=<analyst-virtual-server-id>
ANALYST_CONTEXT_FORGE_TOKEN=<create a token for the Insurance Analysts team>
```

Copy the two `*_VSERVER` values — you will need them in [Step 9](#9-update-agent-assist-environment-variables).

### Option B — Run locally

Set the required variables in your `.env` file and run the script directly:

```bash
# In .env
CONTEXT_FORGE_BASE_URL=https://mcp-context-forge-plugin.<hash>.us-south.codeengine.appdomain.cloud
CONTEXT_FORGE_ADMIN_USERNAME=admin
CONTEXT_FORGE_ADMIN_PASSWORD=<your-admin-password>
MCP_HOST1=https://underwriting-mcp-server.<hash>.us-south.codeengine.appdomain.cloud
MCP_HOST2=https://crm-mcp-server.<hash>.us-south.codeengine.appdomain.cloud
MCP_HOST3=https://health-mcp-server.<hash>.us-south.codeengine.appdomain.cloud

python backend/setup_context_forge.py
```

### Confirm the setup in the Admin UI

After the job completes, the Context Forge gateway should display:

- **3 MCP servers** registered
- **37 tools** registered
- **2 Teams** (Insurance Brokers, Insurance Analysts)
- **2 Virtual servers** (`broker_gateway`, `analysts_gateway`)
- **1 Plugin** enabled (PII filter)

---

## 8. Create Team Tokens

Each team needs a dedicated API token. Tokens control which virtual server an agent can access and what operations it can perform.

Navigate to **Teams** in the Context Forge Admin UI and create one token per team.

### Token for Insurance Brokers

Select the **Insurance Brokers** team, then create a token with:

| Field | Value |
|---|---|
| Name | `BROKER_CONTEXT_FORGE_TOKEN` |
| Virtual server | `broker_gateway` |
| Scopes | `tools.read, resources.read, tools.execute` |

Copy the generated token value — it is shown only once.

### Token for Insurance Analysts

Select the **Insurance Analysts** team, then create a token with:

| Field | Value |
|---|---|
| Name | `ANALYST_CONTEXT_FORGE_TOKEN` |
| Virtual server | `analysts_gateway` |
| Scopes | `tools.read, resources.read, tools.execute` |

Copy the generated token value.

The virtual server IDs (`BROKER_CONTEXT_FORGE_VSERVER` and `ANALYST_CONTEXT_FORGE_VSERVER`) were printed at the end of the setup job logs in Step 7. They are also visible in the Admin UI next to each virtual server.

---

## 9. Update Agent Assist Environment Variables

Once the two tokens have been created in the Context Forge Admin UI (Step 8), go back to `deploy/terraform/agent_assist/terraform.tfvars` and populate all remaining values:

```hcl
# Team tokens (shown once at creation time — copy immediately)
broker_context_forge_token    = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.<broker-payload>.<broker-signature>"
analyst_context_forge_token   = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.<analyst-payload>.<analyst-signature>"

# Virtual server IDs (printed at the end of the setup job logs in Step 7)
broker_context_forge_vserver  = "<broker-virtual-server-id>"
analyst_context_forge_vserver = "<analyst-virtual-server-id>"

# Backend URL — set to the agent-assist endpoint from Step 6 so the browser can reach the API
backend_url  = "https://agent-assist-app.<hash>.us-south.codeengine.appdomain.cloud"

# Enable basic-auth login prompt in the browser
backend_auth     = "true"
backend_user     = "user"
backend_password = "<your-backend-password>"
```

Re-apply the agent-assist module to push all updated environment variables to Code Engine:

```bash
# in deploy/terraform/agent_assist
terraform apply -var-file="terraform.tfvars"
```

Code Engine will perform a rolling restart of the `agent-assist-app` with the updated configuration. After the restart, opening the backend URL in a browser will prompt for the `backend_user` / `backend_password` credentials before granting access.

---

## 10. Test the Application

Open `https://<agent_assist_endpoint>` in your browser.

### Scenario 1 — Direct connection (without Context Forge)

Select **Agent Assist Agentic** and set the connection mode to **Direct MCP**. The agent connects to all three MCP servers simultaneously with no scoping.

Run the following query as the **Broker** persona:

> *Would Lea Kim be eligible for life insurance considering her medical condition?*

Observe the agent trajectory: it may hesitate between tools, query resources outside its intended scope, and produce a longer, less focused response.

### Scenario 2 — With Context Forge

Switch the connection mode to **Context Forge**. Each persona now connects through its own virtual server.

**Broker persona → broker_gateway**

> *Would Lea Kim be eligible for life insurance considering her medical condition?*

The agent calls only the four authorized tools in the correct order: CRM lookup → medical condition → underwriting guidelines.

**Analyst persona → analysts_gateway**

> *Update Lea Kim's address to 1, Place Ville-Marie, Apt 2200, Montréal, Québec, H3B 2C1*

The analyst agent executes the CRM address update. Health and underwriting tools are not visible — they do not exist in the analyst's virtual server.

---

## 11. Check Application Logs

Use `deploy/logs.sh` to tail the logs of any Code Engine application. The script automatically targets the correct resource group and project.

### Login first (if not already done)

```bash
ibmcloud login --sso -a https://cloud.ibm.com -r us-south
```

### Select the Code Engine project

```bash
ibmcloud ce project select --name your-ce-project-name
```

### Fetch logs

```bash
# Usage: sh ./deploy/logs.sh <app-name>
sh ./deploy/logs.sh underwriting-mcp-server
sh ./deploy/logs.sh crm-mcp-server
sh ./deploy/logs.sh health-mcp-server
sh ./deploy/logs.sh mcp-context-forge-plugin
sh ./deploy/logs.sh agent-assist-app
```

The script calls `ibmcloud ce app logs --name <app-name> --all` and streams all available log lines.

### Check setup job run logs

To inspect the output of a `setup-context-forge` job run:

```bash
# List recent job runs
ibmcloud ce jobrun list --job setup-context-forge

# Stream logs of the latest run
ibmcloud ce jobrun logs --jobrun <jobrun-name>
```

---

## Terraform Module Reference

| Module | Directory | Deploys |
|---|---|---|
| MCP Servers | `deploy/terraform/mcp_servers/` | `underwriting-mcp-server`, `crm-mcp-server`, `health-mcp-server` |
| Context Forge | `deploy/terraform/context_forge/` | `redis`, `mcp-context-forge-plugin` |
| Agent Assist | `deploy/terraform/agent_assist/` | `agent-assist-app`, `setup-context-forge` job |

---

## Troubleshooting

| Symptom | Solution |
|---|---|
| `terraform apply` fails with "project not found" | Verify `ce_project_name` matches an existing Code Engine project and that the API key has access to it. |
| `underwriting-mcp-server` never becomes ready | The Chroma store is baked into the image at build time — if the container fails to start, the image may have been built without running `make build-mcp-server` first. Rebuild and push, then redeploy. Check logs with `sh ./deploy/logs.sh underwriting-mcp-server`. |
| Setup job fails with connection errors | Ensure `context_forge_base_url` in `agent_assist/terraform.tfvars` is reachable and the gateway is healthy. Check gateway logs with `sh ./deploy/logs.sh mcp-context-forge-plugin`. |
| Agent-assist returns no tools | Confirm `broker_context_forge_token`, `analyst_context_forge_token`, and both vserver IDs are set in `terraform.tfvars`, then re-run `terraform apply`. |
| Token not accepted by gateway | Tokens are single-use display — if you lost the value, delete the token in the UI and create a new one. |
