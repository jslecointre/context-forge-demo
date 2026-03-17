#!/bin/bash

# ContextForge Insurance Demo - Import Script
# This script imports connections, MCP toolkits, and agents into IBM watsonx Orchestrate
# Usage: ./import-demo-all.sh [connections|toolkits|agents|all]
# Default: imports everything if no argument provided
#
# Prerequisites - set in .env or export before running:
#   WXO_ENV_NAME, WXO_URL, WXO_API_KEY, WXO_SCRIPT_DIR
#   CONTEXT_FORGE_BASE_URL
#   BROKER_CONTEXT_FORGE_VSERVER, BROKER_CONTEXT_FORGE_TOKEN
#   ANALYST_CONTEXT_FORGE_TOKEN, ANALYST_CONTEXT_FORGE_VSERVER
#   (BROKER_CONTEXT_FORGE_URL and ANALYST_CONTEXT_FORGE_URL are derived automatically)

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info()    { printf "${BLUE}ℹ ${NC}%s\n" "$1"; }
print_success() { printf "${GREEN}✓${NC} %s\n" "$1"; }
print_error()   { printf "${RED}✗${NC} %s\n" "$1"; }
print_warning() { printf "${YELLOW}⚠${NC} %s\n" "$1"; }
print_header() {
    printf "\n${BLUE}═══════════════════════════════════════${NC}\n"
    printf "${BLUE}  %s${NC}\n" "$1"
    printf "${BLUE}═══════════════════════════════════════${NC}\n\n"
}

# ---------------------------------------------------------------------------
# Load .env if present
# ---------------------------------------------------------------------------
WXO_SCRIPT_DIR="${WXO_SCRIPT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
ROOT_DIR="${WXO_SCRIPT_DIR}/.."

if [ -f "${ROOT_DIR}/.env" ]; then
    print_info "Loading environment from ${ROOT_DIR}/.env"
    # shellcheck disable=SC1090
    set -a; source "${ROOT_DIR}/.env"; set +a
fi

# Build derived URLs from base URL + virtual server IDs
ANALYST_CONTEXT_FORGE_URL="${CONTEXT_FORGE_BASE_URL}/servers/${ANALYST_CONTEXT_FORGE_VSERVER}/mcp"
BROKER_CONTEXT_FORGE_URL="${CONTEXT_FORGE_BASE_URL}/servers/${BROKER_CONTEXT_FORGE_VSERVER}/mcp"

# ---------------------------------------------------------------------------
# Preflight checks
# ---------------------------------------------------------------------------
check_cli() {
    if ! command -v orchestrate &> /dev/null; then
        print_error "orchestrate CLI not found. Please install it first."
        echo "Visit: https://www.ibm.com/docs/en/watsonx/watson-orchestrate/current?topic=started-installing-cli"
        exit 1
    fi
    print_success "orchestrate CLI found"
}

check_env() {
    local missing=0
    for var in WXO_ENV_NAME WXO_URL WXO_API_KEY \
               CONTEXT_FORGE_BASE_URL \
               BROKER_CONTEXT_FORGE_VSERVER BROKER_CONTEXT_FORGE_TOKEN \
               ANALYST_CONTEXT_FORGE_TOKEN ANALYST_CONTEXT_FORGE_VSERVER; do
        if [ -z "${!var}" ]; then
            print_error "Required env var not set: $var"
            missing=1
        fi
    done
    [ $missing -eq 1 ] && exit 1
    print_success "All required environment variables are set"
}

# ---------------------------------------------------------------------------
# 1. Import Connections
# ---------------------------------------------------------------------------
import_connections() {
    print_header "Step 1 – Importing Connections"

    local connections_dir="${WXO_SCRIPT_DIR}/connections"
    if [ ! -d "$connections_dir" ]; then
        print_warning "Connections directory not found: $connections_dir"
        return
    fi

    orchestrate connections import -f "${connections_dir}/broker_context_forge.yaml"
    print_success "Imported connection: broker_context_forge"

    orchestrate connections import -f "${connections_dir}/analyst_context_forge.yaml"
    print_success "Imported connection: analyst_context_forge"
}

# ---------------------------------------------------------------------------
# 2. Configure Connections & Set Credentials
# ---------------------------------------------------------------------------
configure_credentials() {
    print_header "Step 2 – Configuring Credentials"

    for env in draft live; do
        print_info "Configuring broker_context_forge [$env]"
        orchestrate connections configure \
            -a broker_context_forge \
            --env "$env" \
            --type team \
            --kind bearer

        print_info "Configuring analyst_context_forge [$env]"
        orchestrate connections configure \
            -a analyst_context_forge \
            --env "$env" \
            --type team \
            --kind bearer
    done

    print_info "Setting broker_context_forge credentials"
    orchestrate connections set-credentials -a broker_context_forge --env draft --token "${BROKER_CONTEXT_FORGE_TOKEN}"
    orchestrate connections set-credentials -a broker_context_forge --env live  --token "${BROKER_CONTEXT_FORGE_TOKEN}"
    print_success "broker_context_forge credentials set"

    print_info "Setting analyst_context_forge credentials"
    orchestrate connections set-credentials -a analyst_context_forge --env draft --token "${ANALYST_CONTEXT_FORGE_TOKEN}"
    orchestrate connections set-credentials -a analyst_context_forge --env live  --token "${ANALYST_CONTEXT_FORGE_TOKEN}"
    print_success "analyst_context_forge credentials set"
}

# ---------------------------------------------------------------------------
# 3. Import Virtual MCP Toolkits
# ---------------------------------------------------------------------------
import_toolkits() {
    print_header "Step 3 – Importing Virtual MCP Toolkits"

    print_info "Adding broker_cf_v_mcp_server"
    orchestrate toolkits add \
        --kind mcp \
        --name broker_cf_v_mcp_server \
        --description "Broker MCP ContextForge Virtual Server" \
        --url "${BROKER_CONTEXT_FORGE_URL}" \
        --transport streamable_http \
        --tools "*" \
        --app-id broker_context_forge
    print_success "Added toolkit: broker_cf_v_mcp_server"

    print_info "Adding analyst_cf_v_mcp_server"
    orchestrate toolkits add \
        --kind mcp \
        --name analyst_cf_v_mcp_server \
        --description "Analysts MCP ContextForge Virtual Server" \
        --url "${ANALYST_CONTEXT_FORGE_URL}" \
        --transport streamable_http \
        --tools "*" \
        --app-id analyst_context_forge
    print_success "Added toolkit: analyst_cf_v_mcp_server"
}

# ---------------------------------------------------------------------------
# 4. Import Agents
# ---------------------------------------------------------------------------
import_agents() {
    print_header "Step 4 – Importing Agents"

    local agents_dir="${WXO_SCRIPT_DIR}/agents"
    if [ ! -d "$agents_dir" ]; then
        print_warning "Agents directory not found: $agents_dir"
        return
    fi

    orchestrate agents import -f "${agents_dir}/insurance_analyst_agent.yaml"
    print_success "Imported agent: insurance_analyst_agent"

    orchestrate agents import -f "${agents_dir}/insurance_broker_agent.yaml"
    print_success "Imported agent: insurance_broker_agent"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
    print_header "ContextForge Insurance Demo – Import Script"

    check_cli
    check_env

    local import_type="${1:-all}"

    case "$import_type" in
        connections)
            import_connections
            configure_credentials
            ;;
        toolkits)
            import_toolkits
            ;;
        agents)
            import_agents
            ;;
        all)
            import_connections
            configure_credentials
            import_toolkits
            import_agents
            ;;
        *)
            print_error "Invalid argument: $import_type"
            echo ""
            echo "Usage: $0 [connections|toolkits|agents|all]"
            echo ""
            echo "Options:"
            echo "  connections  - Import connections and set credentials"
            echo "  toolkits     - Import virtual MCP toolkits"
            echo "  agents       - Import agents"
            echo "  all          - Import everything (default)"
            exit 1
            ;;
    esac

    print_header "Import Complete"
    print_success "All imports finished successfully!"
    echo ""
    print_info "Next steps:"
    echo "  1. Verify imports in watsonx Orchestrate UI"
    echo "  2. Test agents with sample interactions"
    echo "  3. Review agent configurations as needed"
    echo ""
}

main "$@"
