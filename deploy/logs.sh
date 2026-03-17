#!/bin/bash
set -e

RESOURCE_GROUP="Default"
CE_PROJECT="wx-ai-gw"
REGION="us-south"
APP_NAME="${1}"

if [[ -z "$APP_NAME" ]]; then
  echo "Usage: $0 <app-name>"
  echo "  e.g. $0 crm-mcp-server"
  echo "       $0 underwriting-mcp-server"
  echo "       $0 health-mcp-server"
  echo "       $0 agent-assist-app"
  echo "       $0 mcp-context-forge-plugin"
  exit 1
fi

echo ">>> Verifying resource group: ${RESOURCE_GROUP}"
RESOURCE_GROUPS_JSON=$(ibmcloud resource groups --output json 2>/dev/null)
MATCHING=$(echo "$RESOURCE_GROUPS_JSON" | jq -r --arg rg "$RESOURCE_GROUP" '.[] | select(.name == $rg) | .name')

if [[ -z "$MATCHING" ]]; then
  echo "ERROR: Resource group '${RESOURCE_GROUP}' does not exist." >&2
  echo "Available resource groups:" >&2
  echo "$RESOURCE_GROUPS_JSON" | jq -r '.[].name' | sed 's/^/  - /' >&2
  exit 1
fi

echo ">>> Targeting resource group: ${RESOURCE_GROUP} / region: ${REGION}"
ibmcloud target -g "${RESOURCE_GROUP}" -r "${REGION}"

echo ">>> Verifying Code Engine project: ${CE_PROJECT}"
TOKEN=$(ibmcloud iam oauth-tokens --output json 2>/dev/null | jq -r '.iam_token')
CE_PROJECTS_JSON=$(curl -s "https://api.${REGION}.codeengine.cloud.ibm.com/v2/projects" \
  -H "Authorization: ${TOKEN}" | jq '.')
PROJECT_ID=$(echo "$CE_PROJECTS_JSON" | jq -r --arg name "$CE_PROJECT" '.projects[] | select(.name == $name) | .id')

if [[ -z "$PROJECT_ID" || "$CE_PROJECT" == "your-project-name" ]]; then
  if [[ "$CE_PROJECT" == "your-project-name" ]]; then
    echo "ERROR: CE_PROJECT is still set to the placeholder 'your-project-name'. Please update the script." >&2
  else
    echo "ERROR: Code Engine project '${CE_PROJECT}' not found in region '${REGION}'." >&2
  fi
  echo "Available projects:" >&2
  echo "$CE_PROJECTS_JSON" | jq -r '.projects[].name' | sed 's/^/  - /' >&2
  exit 1
fi

echo ">>> Selecting Code Engine project: ${CE_PROJECT}"
ibmcloud ce project select -n "${CE_PROJECT}"

echo ">>> Fetching logs for app: ${APP_NAME}"
ibmcloud ce app logs --name "${APP_NAME}" --all
