from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core.models import ModelInfo
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import McpWorkbench, StreamableHttpServerParams
from connection import validate_catalog, validate_live_connection
from fixture.harness import CODE_EXAMPLE, FixtureServer, assert_fixture_result


def names_for(mode: str) -> set[str]:
    return {"demo__lookup_record"} if mode == "tools" else {"weavz_search", "weavz_read_api", "weavz_execute"}


def configured_model_info() -> ModelInfo | None:
    raw_value = os.getenv("WEAVZ_MODEL_INFO")
    if not raw_value:
        return None
    try:
        value = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise RuntimeError("WEAVZ_MODEL_INFO must be valid JSON matching AutoGen ModelInfo") from exc
    if not isinstance(value, dict):
        raise RuntimeError("WEAVZ_MODEL_INFO must be a JSON object matching AutoGen ModelInfo")
    return value  # AutoGen validates the required ModelInfo fields in its client constructor.


async def run_agent(prompt: str, workbench: McpWorkbench) -> object:
    model_id = os.getenv("WEAVZ_MODEL")
    api_key = os.getenv("OPENAI_API_KEY")
    if not model_id or not api_key:
        raise RuntimeError("Set WEAVZ_MODEL and OPENAI_API_KEY for the optional AutoGen run")
    client_config: dict[str, object] = {
        "model": model_id,
        "api_key": api_key,
        "base_url": os.getenv("OPENAI_BASE_URL"),
    }
    model_info = configured_model_info()
    if model_info is not None:
        client_config["model_info"] = model_info
    model_client = OpenAIChatCompletionClient(**client_config)
    try:
        agent = AssistantAgent(
            name="weavz_assistant",
            model_client=model_client,
            workbench=workbench,
            reflect_on_tool_use=True,
        )
        return await agent.run(task=prompt)
    finally:
        await model_client.close()


async def exercise(mode: str, url: str, token: str, *, fixture: bool = False, prompt: str | None = None) -> None:
    params = StreamableHttpServerParams(url=url, headers={"Authorization": f"Bearer {token}"})
    async with McpWorkbench(server_params=params) as workbench:
        tools = await workbench.list_tools()
        names = {tool["name"] for tool in tools}
        validate_catalog(mode, names)
        if fixture and not names_for(mode).issubset(names):
            raise RuntimeError(f"Expected fixture tools {sorted(names_for(mode))}; got {sorted(names)}")
        if not fixture and prompt is None:
            print(json.dumps({"proof": "live Weavz MCP tool discovery", "mode": mode, "tools": sorted(names)}))
            return
        if prompt:
            response = await run_agent(prompt, workbench)
            last = response.messages[-1]
            print(last.content if isinstance(last, TextMessage) else str(last))
            return
        if mode == "tools":
            result = await workbench.call_tool("demo__lookup_record", {"recordId": "record-1"})
            assert_fixture_result(mode, result)
            results = {"lookup": str(result)}
        else:
            search = await workbench.call_tool("weavz_search", {"query": "fixture"})
            read_api = await workbench.call_tool("weavz_read_api", {"alias": "demo", "action": "lookup_record"})
            result = await workbench.call_tool("weavz_execute", {"code": CODE_EXAMPLE})
            assert_fixture_result(mode, search)
            assert_fixture_result(mode, result)
            if "demo" not in json.dumps(read_api, default=str):
                raise AssertionError(f"Unexpected demo API result: {read_api}")
            results = {"search": str(search), "read_api": str(read_api), "execute": str(result)}
        print(json.dumps({"proof": "local fixture AutoGen McpWorkbench calls", "mode": mode, "tools": sorted(names), "results": results}))


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", action="store_true")
    parser.add_argument("--mode", choices=("tools", "code"), default=os.getenv("WEAVZ_MCP_MODE", "tools"))
    parser.add_argument("--prompt")
    args = parser.parse_args()
    if args.fixture:
        if args.prompt:
            raise SystemExit("--prompt uses a model provider; run without --fixture for a live model run")
        with FixtureServer(args.mode) as fixture:
            fixture.reject_bad_token()
            await exercise(args.mode, fixture.url, "local-fixture-token", fixture=True)
    else:
        try:
            url, token = validate_live_connection(os.getenv("WEAVZ_MCP_URL"), os.getenv("WEAVZ_MCP_TOKEN"))
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        await exercise(args.mode, url, token, prompt=args.prompt)


if __name__ == "__main__":
    asyncio.run(main())
