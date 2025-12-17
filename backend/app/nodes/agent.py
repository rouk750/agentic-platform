import json
from app.engine.state import GraphState
from app.services.llm_factory import get_llm_profile, create_llm_instance
from langchain_core.messages import SystemMessage

class GenericAgentNode:
    def __init__(self, node_id: str, config: dict):
        self.node_id = node_id
        self.config = config
        self.profile_id = config.get('profile_id')
        self.label = config.get('label', 'Agent')
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

        # [CRITICAL Fix for Ollama Regression]
        # Some local models (Llama 3, Mistral) via Ollama don't natively realize they have tools bound 
        # unless explicitly told, unlike GPT-4. We inject a hint.
        if profile.provider == "ollama" and self.config.get('tools'):
            effective_system_prompt += "\n\nYou have access to tools. Invoke them using the tool calling format if required to answer."

        # [FEATURE] Prompt Templating (Smart Input Injection)
        # Allow the system prompt to access state variables using {{ variable_name }} syntax.
        # This mirrors the "Smart Node" capability to pull inputs from the state.
        if effective_system_prompt:
            import re
            
            # Find all {{ var_name }} patterns
            pattern = r"\{\{\s*(\w+)\s*\}\}"
            
            def replace_match(match):
                var_name = match.group(1)
                # Look in state first (Priority 1)
                if var_name in state:
                    return str(state[var_name])
                # Look in context dict (Priority 2 - often used in LangGraph)
                if "context" in state and isinstance(state["context"], dict) and var_name in state["context"]:
                    return str(state["context"][var_name])
                
                # Warning if not found, or keep original text?
                # Keeping original text is safer for debugging but might confuse LLM.
                # Let's replace with a placeholder indicating "MISSING" to help user debug
                return f"<{var_name} NOT FOUND>"

            effective_system_prompt = re.sub(pattern, replace_match, effective_system_prompt)
            
            invocation_messages = [SystemMessage(content=effective_system_prompt)] + messages

        from app.engine.debug import print_debug
        
        debug_content = {
            "System Prompt": f"{effective_system_prompt[:200]}..." if effective_system_prompt else "None",
            "Messages Count": len(invocation_messages),
            "Profile": f"ID={profile.id}, Provider={profile.provider}, Model={profile.model_id}, URL={profile.base_url}"
        }
        if invocation_messages:
            debug_content["Last Msg"] = invocation_messages[-1].content[:500]
            
        print_debug(f"DEBUG AGENT {self.label} ({self.node_id})", debug_content)

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
                 try:
                     llm = llm.bind_tools(tools_to_bind)
                 except NotImplementedError:
                     raise ValueError(f"The selected provider ({profile.provider}) or library version does not support tool calling (bind_tools). Please install 'langchain-ollama' or use a different provider.")
                 except Exception as e:
                     print(f"Error binding tools: {e}")
                     # Continue without tools? or raise?
                     # Raising is better to avoid silent failure
                     raise ValueError(f"Failed to bind tools to LLM: {str(e)}")
            
        response = await llm.ainvoke(invocation_messages)
        
        
        # Output Logging
        output_content = {
            "Response": response.content[:500] if response.content else "None",
            "Tool Calls": str(response.tool_calls) if hasattr(response, 'tool_calls') and response.tool_calls else "None"
        }
        print_debug(f"DEBUG AGENT {self.label} ({self.node_id}) [OUTPUT]", output_content)

        # Post-process response for Structured Output
        context_update = {}
        # Parse JSON if schema is requested OR flexible mode is active
        if (self.output_schema or self.flexible_mode) and response.content:
            content_str = str(response.content) # Initialize content_str
            try:
                import re
                # Robust extraction: Look for the first valid JSON block {...}
                json_match = re.search(r"(\{.*\})", content_str, re.DOTALL)
                if json_match:
                    content_str = json_match.group(1)
                else:
                    # Fallback cleanup
                    content_str = content_str.strip()
                    if content_str.startswith("```json"):
                        content_str = content_str[7:]
                    if content_str.endswith("```"):
                        content_str = content_str[:-3]
                
                parsed_json = json.loads(content_str)
                context_update = parsed_json
                
                # Critical Clean Up: Update the message content with the cleaned JSON
                # so downstream nodes (SmartNode) don't get the dirty XML tags.
                response.content = content_str
                
            except (json.JSONDecodeError, AttributeError):
                print(f"Failed to parse JSON output from node {self.node_id}. Content was: {content_str}")
        
        # Tag message with sender Name (Sanitized Label) so Orchestrator recognizes it
        # BUT CRITICAL: If the message has tool_calls, we MUST return it as AIMessage
        # otherwise the Compiler routing will fail to detect the tool call.
        if hasattr(response, 'tool_calls') and response.tool_calls:
             # It's a tool call -> Return as is (AIMessage)
             # We might still want to tag it for logging, but for routing, the type matches.
             # However, LangGraph expects the sender to be set on the message for state tracking.
             response.name = self.label # Set name on AIMessage
             return {"messages": [response], "context": context_update, "last_sender": self.node_id}
        
        import re
        from langchain_core.messages import HumanMessage
        sanitized_name = re.sub(r'[^a-zA-Z0-9_-]', '_', self.label)
        
        # Convert to HumanMessage to force Orchestrator to see it as an external result
        # Add explicit header to help the LLM distinguish it from its own thoughts
        final_content = f"### RESULT FROM {self.label} ###\n{response.content}"
        human_response = HumanMessage(content=final_content, name=sanitized_name)
        
        return {"messages": [human_response], "context": context_update, "last_sender": self.node_id}
