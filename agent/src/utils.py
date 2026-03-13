import json
import inspect
from typing import Any, Optional, Callable
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


ToolStartHook = Callable[[str, str, str], Any]
ToolSuccessHook = Callable[[str, str, str], Any]
ToolFailureHook = Callable[[str, str, str], Any]


class AgentRunner:
    def __init__(
        self,
        client: OpenAI,
        model: str,
        local_tool_map: dict[str, Callable[..., Any]],
        tools: Optional[list[Any]] = None,
        mcp: Optional[StdioServerParameters] = None,
    ) -> None:
        self.client = client
        self.model = model
        self.local_tool_map = local_tool_map
        self.tools = tools or []
        self.mcp = mcp

    def mcp_tools_to_openai_tools(self, mcp_tools: list[Any]) -> list[dict[str, Any]]:
        tools: list[dict[str, Any]] = []
        for tool in mcp_tools:
            tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.inputSchema or {"type": "object", "properties": {}},
                }
            })

        return tools

    def normalize_mcp_content(self, result: Any) -> str:
        if hasattr(result, "structuredContent") and result.structuredContent is not None:
            return json.dumps(result.structuredContent, ensure_ascii=False)

        if hasattr(result, "content") and result.content:
            chunks = []
            for item in result.content:
                text = getattr(item, "text", None)
                if text:
                    chunks.append(text)
                else:
                    chunks.append(str(item))
            return "\n".join(chunks)

        return str(result)

    async def _run_hook(self, hook: Optional[Callable[..., Any]], *args: Any) -> None:
        if hook is None:
            return
        result = hook(*args)
        if inspect.isawaitable(result):
            await result

    async def execute_tool_call(
        self,
        tool_call: Any,
        mcp_session: Optional[ClientSession] = None,
        on_tool_start: Optional[ToolStartHook] = None,
        on_tool_success: Optional[ToolSuccessHook] = None,
        on_tool_failure: Optional[ToolFailureHook] = None,
    ) -> dict[str, Any]:
        tool_name = tool_call.function.name
        raw_args = tool_call.function.arguments or "{}"
        tool_call_id = tool_call.id

        await self._run_hook(on_tool_start, tool_call_id, tool_name, raw_args)

        try:
            args = json.loads(raw_args)
        except json.JSONDecodeError:
            args = {}
        try:
            if tool_name in self.local_tool_map:
                result = self.local_tool_map[tool_name](**args)

                if hasattr(result, "__await__"):
                    result = await result
                content = str(result)
                await self._run_hook(on_tool_success, tool_call_id, tool_name, content)
                return {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": content,
                }
            if mcp_session is not None:
                result = await mcp_session.call_tool(tool_name, args)
                content = self.normalize_mcp_content(result)
                await self._run_hook(on_tool_success, tool_call_id, tool_name, content)
                return {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": content,
                }

            raise ValueError(f"Unknown tool: {tool_name}")
        except Exception as exc:
            await self._run_hook(on_tool_failure, tool_call_id, tool_name, str(exc))
            raise

    async def handle_tool_calls(
        self,
        message: Any,
        mcp_session: Optional[ClientSession] = None,
        on_tool_start: Optional[ToolStartHook] = None,
        on_tool_success: Optional[ToolSuccessHook] = None,
        on_tool_failure: Optional[ToolFailureHook] = None,
    ) -> list[dict[str, Any]]:
        responses = []
        for tool_call in message.tool_calls:
            tool_response = await self.execute_tool_call(
                tool_call=tool_call,
                mcp_session=mcp_session,
                on_tool_start=on_tool_start,
                on_tool_success=on_tool_success,
                on_tool_failure=on_tool_failure,
            )
            responses.append(tool_response)

        return responses

    async def agent_loop(
        self,
        messages: list[dict[str, Any]],
        tools: Optional[list[Any]] = None,
        mcp_session: Optional[ClientSession] = None,
        on_tool_start: Optional[ToolStartHook] = None,
        on_tool_success: Optional[ToolSuccessHook] = None,
        on_tool_failure: Optional[ToolFailureHook] = None,
    ) -> Any:
        active_tools = tools if tools is not None else self.tools
        while True:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=active_tools,
                tool_choice="auto",
            )
            message = response.choices[0].message

            messages.append(message.model_dump(exclude_none=True))
            if not message.tool_calls:
                return message.content
            responses = await self.handle_tool_calls(
                message=message,
                mcp_session=mcp_session,
                on_tool_start=on_tool_start,
                on_tool_success=on_tool_success,
                on_tool_failure=on_tool_failure,
            )

            messages.extend(responses)

    async def run_agent(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: Optional[list[Any]] = None,
        mcp: Optional[StdioServerParameters] = None,
        on_tool_start: Optional[ToolStartHook] = None,
        on_tool_success: Optional[ToolSuccessHook] = None,
        on_tool_failure: Optional[ToolFailureHook] = None,
    ) -> Any:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        all_tools = (tools if tools is not None else self.tools).copy()
        active_mcp = mcp if mcp is not None else self.mcp

        if active_mcp:
            async with stdio_client(active_mcp) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    mcp_tool_list = (await session.list_tools()).tools
                    all_tools.extend(self.mcp_tools_to_openai_tools(mcp_tool_list))
                    return await self.agent_loop(
                        messages=messages,
                        tools=all_tools,
                        mcp_session=session,
                        on_tool_start=on_tool_start,
                        on_tool_success=on_tool_success,
                        on_tool_failure=on_tool_failure,
                    )

        return await self.agent_loop(
            messages=messages,
            tools=all_tools,
            mcp_session=None,
            on_tool_start=on_tool_start,
            on_tool_success=on_tool_success,
            on_tool_failure=on_tool_failure,
        )

    async def run(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: Optional[list[Any]] = None,
        mcp: Optional[StdioServerParameters] = None,
        on_tool_start: Optional[ToolStartHook] = None,
        on_tool_success: Optional[ToolSuccessHook] = None,
        on_tool_failure: Optional[ToolFailureHook] = None,
    ) -> Any:
        return await self.run_agent(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            tools=tools,
            mcp=mcp,
            on_tool_start=on_tool_start,
            on_tool_success=on_tool_success,
            on_tool_failure=on_tool_failure,
        )
