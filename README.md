# AutoGen MCP integration examples with Weavz

<!-- weavz:discovery:start -->

Connect AutoGen to GitHub, Slack, Jira Cloud and Gmail through a remote Weavz Model Context Protocol (MCP) server. Use the native MCP adapter, then try the app setup recipes with your configured connections.

App setup recipes:

- [GitHub MCP with AutoGen Python](docs/app-recipes.md#github-mcp-with-autogen-python)
- [Slack MCP with AutoGen Python](docs/app-recipes.md#slack-mcp-with-autogen-python)
- [Jira Cloud MCP with AutoGen Python](docs/app-recipes.md#jira-cloud-mcp-with-autogen-python)
- [Gmail MCP with AutoGen Python](docs/app-recipes.md#gmail-mcp-with-autogen-python)

The framework consumes app tools from your configured Weavz MCP server. App recipes require your own app connections; automated checks use synthetic records.

[MCP app and framework directory](https://github.com/weavz/mcp-examples/blob/main/docs/integrations.md) · [All examples](https://github.com/weavz/mcp-examples) · [Weavz MCP guide](https://weavz.io/docs/guides/agent-framework-examples)

<!-- weavz:discovery:end -->

Connects Microsoft's AutoGen AgentChat through the native `McpWorkbench` and Streamable HTTP adapter. Configure a custom Weavz MCP server in Tools Mode or Code Mode first; the `--mode` option verifies tools from the configured server. The personal `/mcp/weavz` connector uses OAuth and does not accept a copied MCP bearer token.

Requires Python 3.11 or 3.12 and uv. `WEAVZ_MCP_TOKEN` must be an MCP access token, not a Weavz REST API key.

```sh
uv sync --locked
uv run python main.py --fixture --mode tools
uv run python main.py --fixture --mode code
uv run pytest
```

The fixture checks run without a model against a separate local bearer-protected MCP SDK server and synthetic data. For live discovery, copy `.env.example` to `.env` and use `uv run --env-file .env python main.py --mode tools` or `--mode code`. To run the optional AutoGen agent, connect an app with task-relevant records and set `WEAVZ_MODEL` and `OPENAI_API_KEY` (plus `OPENAI_BASE_URL` for compatible endpoints). AutoGen infers capability metadata for model IDs it recognizes; for an unknown/custom ID, it requires `WEAVZ_MODEL_INFO` as a JSON object matching AutoGen's native `ModelInfo` fields: `vision`, `function_calling`, `json_output`, `structured_output`, and `family`. Set these capability values from your provider's model documentation; this example does not guess them. Then add `--prompt "Summarize the records relevant to my current task"`.
