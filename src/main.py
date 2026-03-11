import json
import operator
import os
from pathlib import Path
from typing import Literal

from langchain.messages import AnyMessage, SystemMessage, ToolMessage
from langchain.tools import tool
from langchain_core.messages import messages_to_dict
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph
from typing_extensions import Annotated, TypedDict

model = ChatOpenAI(
    base_url=os.getenv("AZURE_OPENAI_ENDPOINT") + "/openai/v1",
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
)


# Define tools
@tool
def multiply(a: int, b: int) -> int:
    """Multiply `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a * b


@tool
def add(a: int, b: int) -> int:
    """Adds `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a + b


@tool
def divide(a: int, b: int) -> float:
    """Divide `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a / b


# Augment the LLM with tools
tools = [add, multiply, divide]
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = model.bind_tools(tools)


class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int


def llm_call(state: dict):
    """LLM decides whether to call a tool or not"""

    return {
        "messages": [
            model_with_tools.invoke(
                [
                    SystemMessage(
                        content="You are a helpful assistant tasked with performing arithmetic on a set of inputs."
                    )
                ]
                + state["messages"]
            )
        ],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


def tool_node(state: dict):
    """Performs the tool call"""

    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
    return {"messages": result}


def should_continue(state: MessagesState) -> Literal["tool_node", END]:
    """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""

    messages = state["messages"]
    last_message = messages[-1]

    # If the LLM makes a tool call, then perform an action
    if last_message.tool_calls:
        return "tool_node"

    # Otherwise, we stop (reply to the user)
    return END


DB_URI = f"postgresql://postgres:{os.getenv('POSTGRES_PASSWORD')}@localhost:5432/postgres?sslmode=disable"
with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    # Note: You need to call checkpointer.setup() the first time you’re using Postgres checkpointer
    # checkpointer.setup()

    # Build workflow
    agent_builder = StateGraph(MessagesState)

    # Add nodes
    agent_builder.add_node("llm_call", llm_call)
    agent_builder.add_node("tool_node", tool_node)

    # Add edges to connect nodes
    agent_builder.add_edge(START, "llm_call")
    agent_builder.add_conditional_edges("llm_call", should_continue, ["tool_node", END])
    agent_builder.add_edge("tool_node", "llm_call")

    # Compile the agent
    agent = agent_builder.compile(checkpointer=checkpointer)

    # Show the agent
    graph_png = agent.get_graph(xray=True).draw_mermaid_png()
    outputs_dir = Path(__file__).resolve().parent.parent / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    output_path = outputs_dir / "agent_graph.png"
    output_path.write_bytes(graph_png)
    print(f"Saved agent graph to: {output_path}")

    # Invoke

    config = {"configurable": {"thread_id": "1"}}
    # messages = [HumanMessage(content="Add 3 and 4 and multiply result by 5")]
    # messages = agent.invoke({"messages": messages}, config=config)
    # for m in messages["messages"]:
    #     m.pretty_print()

    # State export
    state_history = list(agent.get_state_history(config))
    export = []
    for snapshot in state_history:
        entry = {
            "config": snapshot.config,
            "parent_config": snapshot.parent_config,
            "created_at": snapshot.created_at,
            "next": list(snapshot.next),
            "messages": messages_to_dict(snapshot.values.get("messages", [])),
            "llm_calls": snapshot.values.get("llm_calls"),
        }
        export.append(entry)
    export_path = outputs_dir / "state_export.json"
    export_path.write_text(json.dumps(export, indent=2, default=str))
    print(f"Saved {len(export)} state snapshots to: {export_path}")
