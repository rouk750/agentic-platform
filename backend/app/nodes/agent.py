import json
from app.engine.state import GraphState
from app.services.llm_factory import get_llm_profile, create_llm_instance
from langchain_core.messages import SystemMessage

class GenericAgentNode:
    def __init__(self, node_id: str, config: dict):
        self.node_id = node_id
        self.config = config
        self.profile_id = config.get('profile_id')
        self.system_prompt = config.get('system_prompt', "")
        self.output_schema = config.get('output_schema', [])
        self.flexible_mode = config.get('flexible_mode', False)
        # Max iterations loop protection
        self.max_iterations = config.get('max_iterations')
        if self.max_iterations:
            try:
                self.max_iterations = int(self.max_iterations)
            except ValueError:
                self.max_iterations = 0 # Disable if invalid
        
    async def __call__(self, state: GraphState):
        messages = state["messages"]
        
        # Check iteration limit
        if self.max_iterations and self.max_iterations > 0:
            count = sum(1 for m in messages if hasattr(m, 'name') and m.name == self.node_id)
            if count >= self.max_iterations:
                raise ValueError(f"Agent '{self.node_id}' reached max iterations limit ({self.max_iterations}).")
        
        # Hydrate LLM
        if not self.profile_id:
             # Fallback: Try to get the first available profile
             # This is a "Playground" convenience.
             from app.services.llm_factory import get_first_profile
             try:
                 fallback_profile = get_first_profile()
                 if fallback_profile:
                     self.profile_id = fallback_profile.id
                 else:
                     raise ValueError(f"Node {self.node_id} has no profile_id configured and no default found.")
             except Exception:
                 raise ValueError(f"Node {self.node_id} has no profile_id configured")
             
        profile = get_llm_profile(self.profile_id)
        llm = create_llm_instance(profile)
        
        # Prepare messages
        invocation_messages = messages
        
        # Handle Output Schema (JSON Mode fallback)
        effective_system_prompt = self.system_prompt
        
        if self.flexible_mode:
            # Flexible Mode: Orchestrator style
            # We don't enforce a rigid schema, but we demand JSON.
            effective_system_prompt += "\n\nIMPORTANT: You must output a valid JSON object. The structure depends on your decision (e.g. tool call or final answer). Do not include markdown formatting like ```json. Just raw JSON."
        elif self.output_schema:
            # Rigid Schema Mode
            schema_instruction = "\n\nIMPORTANT: You must output a valid JSON object matching this schema:\n{\n"
            for field in self.output_schema:
                schema_instruction += f'  "{field["name"]}": "{field["type"]} - {field["description"]}",\n'
            schema_instruction += "}\nDo not include markdown formatting like ```json. Just raw JSON."
            effective_system_prompt += schema_instruction

        if effective_system_prompt:
             invocation_messages = [SystemMessage(content=effective_system_prompt)] + messages

        # Bind tools if any
        # The frontend sends a list of tool names in config['tools']
        tool_names = self.config.get('tools', [])
        if tool_names:
             from app.services.tool_registry import get_tool
             tools_to_bind = []
             for name in tool_names:
                 tool_instance = await get_tool(name)
                 if tool_instance:
                     tools_to_bind.append(tool_instance)
                 else:
                     print(f"Warning: Tool {name} not found in registry.")
             
             if tools_to_bind:
                 llm = llm.bind_tools(tools_to_bind)
            
        response = await llm.ainvoke(invocation_messages)
        
        # Post-process response for Structured Output
        context_update = {}
        # Parse JSON if schema is requested OR flexible mode is active
        if (self.output_schema or self.flexible_mode) and response.content:
            try:
                # Naive JSON extraction (strip markdown if model ignores instruction)
                content_str = str(response.content).strip()
                if content_str.startswith("```json"):
                    content_str = content_str[7:]
                if content_str.endswith("```"):
                    content_str = content_str[:-3]
                
                parsed_json = json.loads(content_str)
                context_update = parsed_json
            except json.JSONDecodeError:
                print(f"Failed to parse JSON output from node {self.node_id}")
        
        # Tag message with sender ID for tracking
        response.name = self.node_id
        
        return {"messages": [response], "context": context_update, "last_sender": self.node_id}
