"""
Agent entrypoint. Launches the MCP server as a subprocess, discovers
its tools dynamically, then runs a ReAct loop where the LLM decides
which tool to call next based on what it's learned so far.

CLI usage:      python agent/main.py --container-id MAEU1234567
Programmatic:   from agent.main import run_agent
                 result = await run_agent("MAEU1234567")
(used by api/main.py's POST /shipments/{id}/investigate endpoint)
"""

import argparse
import asyncio
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

sys.path.insert(0, os.path.dirname(__file__))
from prompts import SYSTEM_PROMPT, USER_TURN_TEMPLATE
from reasoning import ask_llm
from state import AgentState

SERVER_SCRIPT = os.path.join(os.path.dirname(__file__), "..", "mcp_server", "server.py")
SERVER_CWD = os.path.join(os.path.dirname(__file__), "..", "mcp_server")


def format_tool_list(tools) -> str:
    return "\n".join(f"- {t.name}: {t.description}" for t in tools)


async def run_agent(container_id: str, verbose: bool = True) -> dict:
    server_params = StdioServerParameters(
        command="python",
        args=[SERVER_SCRIPT],
        cwd=SERVER_CWD,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools_result = await session.list_tools()
            tool_list_text = format_tool_list(tools_result.tools)
            tool_names = {t.name for t in tools_result.tools}

            system_prompt = SYSTEM_PROMPT.format(tool_list=tool_list_text)
            state = AgentState(max_iterations=10)

            if verbose:
                print("=== Shipment Exception Resolution Agent ===")
                print(f"Investigating container: {container_id}")
                print(f"Discovered {len(tool_names)} tools:\n{tool_list_text}\n")

            state.record(
                "system_note", {}, "context",
                f"Investigate container_id={container_id}. Start with get_shipment_details.",
            )

            while not state.finished and state.iteration < state.max_iterations:
                state.iteration += 1
                user_prompt = USER_TURN_TEMPLATE.format(
                    attempt=state.iteration,
                    max_attempts=state.max_iterations,
                    history=state.history_as_text(),
                )

                try:
                    decision = ask_llm(system_prompt, user_prompt)
                except ValueError as e:
                    if verbose:
                        print(f"[iter {state.iteration}] LLM output unparseable: {e}")
                    continue

                action = decision.get("action")
                reasoning = decision.get("reasoning", "")

                if action == "finish":
                    claimed_success = decision.get("success", False)
                    status_updated = state.called("update_shipment_status", "Updated")
                    notified = state.called("draft_customer_notification", "Notification drafted")

                    if claimed_success and not (status_updated and notified):
                        missing = []
                        if not status_updated:
                            missing.append("update_shipment_status")
                        if not notified:
                            missing.append("draft_customer_notification")
                        msg = f"REJECTED: required AWS step(s) not completed: {', '.join(missing)}"
                        if verbose:
                            print(f"[iter {state.iteration}] finish rejected: {msg}")
                        state.record("finish", {}, reasoning, msg)
                        continue

                    state.finished = True
                    state.success = claimed_success
                    state.summary = decision.get("summary", "")
                    break

                if action not in tool_names:
                    if verbose:
                        print(f"[iter {state.iteration}] LLM picked unknown tool '{action}', skipping")
                    continue

                args = decision.get("args", {})
                if verbose:
                    print(f"[iter {state.iteration}] -> {action}({args})  # {reasoning}")

                try:
                    result = await session.call_tool(action, arguments=args)
                    observation = "\n".join(
                        block.text for block in result.content if hasattr(block, "text")
                    )
                except Exception as e:
                    observation = f"ERROR calling {action}: {e}"

                if verbose:
                    print(f"    observation: {observation[:300]}")
                state.record(action, args, reasoning, observation)

            if verbose:
                print("\n=== RUN COMPLETE ===")
                print(f"Success: {state.success}")
                print(f"Summary: {state.summary}")
                print(f"Iterations used: {state.iteration}/{state.max_iterations}")

            return {
                "container_id": container_id,
                "success": state.success,
                "summary": state.summary,
                "iterations_used": state.iteration,
                "max_iterations": state.max_iterations,
                "history": state.history,
            }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--container-id", required=True)
    args = parser.parse_args()
    asyncio.run(run_agent(args.container_id))
