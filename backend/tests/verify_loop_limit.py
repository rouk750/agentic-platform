import sys
import os
import asyncio
from typing import Dict, Any

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.nodes.agent import GenericAgentNode
from app.engine.state import GraphState
from langchain_core.messages import HumanMessage, AIMessage

# Mock GraphState
def create_state(messages):
    return {
        "messages": messages,
        "context": {},
        "last_sender": None
    }

async def verify_loop_limits():
    print("Testing Per-Agent Loop Limits...")
    
    node_id = "agent_TEST"
    max_iters = 2
    
    # 1. Initialize Node with limit
    config = {
        "profile_id": "mock_profile", # Will fail if tries to hydrate, but we want to fail fast on limit check
        "max_iterations": max_iters
    }
    
    # We need to mock get_llm_profile or handle the failure gracefully if we want to reach the LLM part
    # But wait, the check is BEFORE LLM hydration.
    # So we don't need a real LLM profile if we trigger the limit!
    
    agent = GenericAgentNode(node_id, config)
    
    # 2. Simulate state with messages FROM this agent equal to limit
    messages_at_limit = [
        HumanMessage(content="Start"),
        AIMessage(content="Rep 1", name=node_id),
        HumanMessage(content="User reply"),
        AIMessage(content="Rep 2", name=node_id)
    ]
    
    # Total from agent_TEST = 2. Limit = 2. 
    # Calling it again should trigger error because count (2) >= limit (2).
    # Wait, if limit is 2, does it mean it can Produce 2 messages or it stops after 2?
    # Logic: "if count >= self.max_iterations: raise"
    # Existing = 2. 
    # If we call it, it tries to produce the 3rd. 
    # So if max_iters=2, we expect it to allow 2. If we try 3rd, it fails.
    
    state = create_state(messages_at_limit)
    
    try:
        print(f" invoking agent with {max_iters} previous msgs (limit={max_iters})...")
        await agent(state)
        print("❌ Failed: Agent should have raised ValueError but proceeded.")
        return False
    except ValueError as e:
        if "reached max iterations limit" in str(e):
            print(f"✅ Success: Correctly caught limit.\n   Error: {e}")
            return True
        else:
             print(f"❌ Failed: Raised wrong ValueError: {e}")
             return False
    except Exception as e:
        # It might fail on profile_id missing if the check passed (which is bad)
        if "profile_id configured" in str(e):
             print("❌ Failed: Limit check passed (it tried to hydrate LLM) despite limit reached.")
             return False
        print(f"❌ Failed: Unexpected exception: {e}")
        return False

if __name__ == "__main__":
    if asyncio.run(verify_loop_limits()):
        sys.exit(0)
    else:
        sys.exit(1)
