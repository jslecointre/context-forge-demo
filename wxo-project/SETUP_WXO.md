### Deploy to IBM watsonx Orchestrate

This deploys two AI agents (Insurance Broker and Insurance Analyst) into watsonx Orchestrate, connected to the ContextForge virtual MCP servers.

**Prerequisites**

- [watsonx Orchestrate CLI](https://www.ibm.com/docs/en/watsonx/watson-orchestrate/current?topic=started-installing-cli) installed
- A running ContextForge instance (see step 2 above or the Cloud deployment)

**Configure environment**

Add the following WXO-specific variables to the main `.env` file at the project root (ContextForge variables should already be set):

```bash
WXO_ENV_NAME=<your-wxo-env-name>
WXO_URL=https://api.us-south.watson-orchestrate.cloud.ibm.com/instances/<instance-id>
WXO_API_KEY=<your-api-key>
WXO_SCRIPT_DIR=/path/to/wxo-project
```

**Configure the watsonx Orchestrate environment**

Register and activate your WXO environment (first time setup):

```bash
orchestrate env add -n ${WXO_ENV_NAME} -u ${WXO_URL} --type ibm_iam --activate
```

On subsequent sessions, just activate the existing environment:

```bash
orchestrate env activate ${WXO_ENV_NAME}
```

**Deploy all assets**

```bash
cd wxo-project
./import-demo-all.sh        # deploys connections, MCP toolkits, and agents
./import-demo-all.sh agents # deploy agents only
```

**Tear down**

```bash
./delete-demo-all.sh        # removes agents, MCP toolkits, and connections
./delete-demo-all.sh agents # remove agents only
```

---
