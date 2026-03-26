import json
import time
import streamlit as st
import anthropic

from tools import TOOLS, SYSTEM_PROMPT
from sam_api import get_today_date, search_opportunities, search_contract_awards


def _call_claude_with_retry(client: anthropic.Anthropic, **kwargs):
    """Call the Claude API with automatic backoff on rate limit errors."""
    for attempt in range(3):
        try:
            return client.messages.create(**kwargs)
        except anthropic.RateLimitError:
            if attempt < 2:
                wait = (attempt + 1) * 10  # 10s then 20s
                st.toast(f"⏳ Rate limit hit — retrying in {wait}s…", icon="⏳")
                time.sleep(wait)
            else:
                raise


def _dispatch_tool(tc, sam_api_key: str) -> dict:
    """Route a tool call to the correct SAM.gov function."""
    if tc.name == "get_today_date":
        return get_today_date()
    elif tc.name == "search_opportunities":
        return search_opportunities(api_key=sam_api_key, **tc.input)
    elif tc.name == "search_contract_awards":
        return search_contract_awards(api_key=sam_api_key, **tc.input)
    else:
        return {"error": f"Unknown tool: {tc.name}"}


def run_agent(user_message: str, sam_api_key: str, anthropic_api_key: str) -> str:
    """
    Run the agentic loop:
      1. Send the user message to Claude.
      2. If Claude calls tools, execute them against SAM.gov.
      3. Feed results back and repeat until Claude produces a final answer.
    Returns the final text response.
    """
    client = anthropic.Anthropic(api_key=anthropic_api_key)
    messages = [{"role": "user", "content": user_message}]
    status = st.empty()
    result_text = ""

    for _ in range(6):  # max 6 tool rounds
        status.info("🤔 Thinking…")

        response = _call_claude_with_retry(
            client,
            model="claude-sonnet-4-20250514",
            max_tokens=2048,          # reduced from 4096 to cut output tokens
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        tool_calls, text_blocks = [], []
        for block in response.content:
            if block.type == "text":
                text_blocks.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(block)

        result_text = "\n".join(text_blocks)

        if response.stop_reason == "end_turn" or not tool_calls:
            break

        tool_results = []
        for tc in tool_calls:
            status.info(f"🔍 Querying SAM.gov — `{tc.name}`…")

            with st.expander(f"🔧 Tool call: `{tc.name}`", expanded=False):
                st.json(tc.input)

            output = _dispatch_tool(tc, sam_api_key)

            with st.expander(f"📦 Result: `{tc.name}`", expanded=False):
                st.json(output)

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tc.id,
                "content": json.dumps(output),
            })

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    status.empty()
    return result_text or "I wasn't able to find relevant results. Please try rephrasing your question."
