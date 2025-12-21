import json
from app.engine.state import GraphState
from app.services.llm_factory import get_llm_profile, create_llm_instance
from langchain_core.messages import SystemMessage
from app.utils.text_processing import sanitize_label, render_template

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
        
        # [CRITICAL FIX] Context Isolation for Sub-Agents (Agent-as-a-Tool)
        # If the last message is a Tool Call directed at THIS agent, we must NOT pass the full history.
        # Why? Because the LLM sees the Orchestrator's "Call tool rzouga" message and gets confused, 
        # often hallucinating a new tool call to itself instead of answering.
        # Solution: Extract the 'query' argument and present it as a fresh User Message.
        
        last_msg = messages[-1] if messages else None
        incoming_tool_call_id = None
        
        if last_msg and hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
            sanitized_self_name = sanitize_label(self.label)
            
            for tc in last_msg.tool_calls:
                tc_name = tc.get('name')
                # Check if this tool call is for us
                if tc_name in [self.label, sanitized_self_name, self.node_id]:
                    incoming_tool_call_id = tc.get('id')
                    args = tc.get('args', {})
                    query = args.get('query') or args.get('question') or str(args)
                    
                    query = args.get('query') or args.get('question') or str(args)
                    
                    # [CONTEXT ISOLATION]
                    # We extract only the query to prevent the sub-agent from seeing the parent's conversation history.
                    # This prevents confusion and recursive hallucinations.
                    # print(f"DEBUG AGENT {self.node_id}: Context Isolation Active. Extracted query: {query}")
                    
                    from langchain_core.messages import HumanMessage
                    
                    from langchain_core.messages import HumanMessage
                    # Replace history with just this query
                    invocation_messages = [HumanMessage(content=query)]
                    break
        
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
        # [FEATURE] Prompt Templating (Smart Input Injection)
        # Allow the system prompt to access state variables using {{ variable_name }} syntax.
        # This mirrors the "Smart Node" capability to pull inputs from the state.
        if effective_system_prompt:
             # Merge state and context for template rendering
             # Priority: state vars, then context vars
             template_context = {}
             if "context" in state and isinstance(state["context"], dict):
                 template_context.update(state["context"])
             template_context.update(state)
             
             effective_system_prompt = render_template(effective_system_prompt, template_context)
             
             invocation_messages = [SystemMessage(content=effective_system_prompt)] + invocation_messages

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
             print(f"DEBUG AGENT {self.node_id}: Attempting to bind tools: {tool_names}")
             from app.services.tool_registry import get_tool
             tools_to_bind = []
             for name in tool_names:
                 tool_instance = await get_tool(name)
                 if tool_instance:
                     tools_to_bind.append(tool_instance)
                 else:
                     print(f"Warning: Tool {name} not found in registry. creating virtual tool.")
                     # ... [Virtual Tool Logic] ...
                     # [CRITICAL FIX] Virtual Tool Binding for Sub-Agents
                     # If the tool is not found in the registry, we assume it's another Agent connected in the graph.
                     # We create a "Virtual Tool" so the LLM has a valid schema to generate a tool_call against.
                     try:
                         from app.utils.tool_utils import create_virtual_tool
                         virtual_tool = create_virtual_tool(name)
                         tools_to_bind.append(virtual_tool)
                         print(f"DEBUG: Created Virtual Tool for agent '{name}'")
                     except Exception as vt_e:
                         print(f"Error creating virtual tool for {name}: {vt_e}")
             
             if tools_to_bind:
                 print(f"DEBUG AGENT {self.node_id}: Final tools bound: {[t.name for t in tools_to_bind]}")
                 try:
                     llm = llm.bind_tools(tools_to_bind)
                 except NotImplementedError:
                     raise ValueError(f"The selected provider ({profile.provider}) or library version does not support tool calling (bind_tools). Please install 'langchain-ollama' or use a different provider.")
                 except Exception as e:
                     print(f"Error binding tools: {e}")
                     # Continue without tools? or raise?
                     # Raising is better to avoid silent failure
                     raise ValueError(f"Failed to bind tools to LLM: {str(e)}")
            
        
        # [FEATURE] Self-Correction Loop for Recursive Hallucinations
        # Some models (like gpt-oss) will try to call themselves as a tool when asked to perform their expert function.
        # We need to catch this, tell the model "Stop it", and retry.
        
        # [FEATURE] Hallucination Correction Loop
        # Catch Self-Calls (Recursive) AND Unbound Tools (Hallucinations)
        
        current_messages = invocation_messages
        response = None
        bound_tool_names = [t.name for t in tools_to_bind] if 'tools_to_bind' in locals() else []
        
        # Try up to 3 times (Initial + 2 Retries)
        for attempt in range(3):
            response = await llm.ainvoke(current_messages)
            
            # Check for Hallucinated Tool Calls
            if hasattr(response, 'tool_calls') and response.tool_calls:
                bad_tool_detected = False
                bad_tool_name = ""
                sanitized_self_name = sanitize_label(self.label)
                
                for tc in response.tool_calls:
                   tn = tc.get('name')
                   # Check 1: Self Call
                   if tn in [self.label, sanitized_self_name, self.node_id]:
                       bad_tool_detected = True
                       bad_tool_name = tn
                   if tn in [self.label, sanitized_self_name, self.node_id]:
                       bad_tool_detected = True
                       bad_tool_name = tn
                       # print(f"DEBUG AGENT {self.node_id}: Detected Self-Call to '{tn}'")
                       break
                   # Check 2: Unbound Tool (Hallucination)
                   if tn not in bound_tool_names:
                       bad_tool_detected = True
                       bad_tool_name = tn
                       # print(f"DEBUG AGENT {self.node_id}: Detected Unbound Tool Call to '{tn}' (Available: {bound_tool_names})")
                       break
                
                if bad_tool_detected:
                    # [ANTI-HALLUCINATION CONFIG]
                    # If the agent tries to call itself or a non-existent tool, we intercept it.
                    # print(f"DEBUG AGENT {self.node_id}: Hallucination detected (Attempt {attempt+1}/3).")
                    
                    if attempt == 2:
                        # Hard Fallback
                        print(f"DEBUG AGENT {self.node_id}: Max retries reached. Forcing text fallback.")
                        from langchain_core.messages import AIMessage
                        fallback_text = f"I am {self.label}. I cannot use the tool '{bad_tool_name}' as requested. Here is my answer based on my knowledge."
                        response = AIMessage(content=fallback_text)
                        response.tool_calls = []
                        break
                    
                    # Retry with Error
                    error_content = f"CRITICAL ERROR: The tool '{bad_tool_name}' is NOT available. You must Answer the user's question DIRECTLY in text. Do not call any tools."
                    error_msg = SystemMessage(content=error_content)
                    current_messages = list(current_messages) + [response, error_msg]
                    continue 
            
            break

        
        
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
            content_str = str(response.content) # Initialize content_str
            from app.utils.text_processing import extract_json_from_text
            
            parsed_json = extract_json_from_text(content_str)
            if parsed_json:
                context_update = parsed_json
                # Updating response content might be tricky if we want to keep original text vs clean JSON
                # But previous logic did update it. Let's keep it consistent if extract_json works.
                # Actually extract_json returns Dict, not string.
                response.content = json.dumps(parsed_json) 
            else:
                 print(f"Failed to parse JSON output from node {self.node_id}. Content was: {content_str}")
        
        # Tag message with sender Name (Sanitized Label) so Orchestrator recognizes it
        # BUT CRITICAL: If the message has tool_calls, we MUST return it as AIMessage
        if hasattr(response, 'tool_calls') and response.tool_calls:
             response.name = self.label 
             return {"messages": [response], "context": context_update, "last_sender": self.node_id}
        
        # [CRITICAL FIX] Agent-as-a-Tool Polymorphic Return
        # If this agent was invoked by a Tool Call (from an Orchestrator), we MUST return a ToolMessage.
        # Otherwise, the Orchestrator will see an AIMessage (Tool Call) followed by a HumanMessage, 
        # leaving the Tool Call 'unresolved' and confusing the LLM history.
        
        last_input_message = invocation_messages[-1] if invocation_messages else None
        is_tool_invocation = False
        tool_call_id = None
        
        sanitized_name = sanitize_label(self.label)
        
        if last_input_message and hasattr(last_input_message, 'tool_calls') and last_input_message.tool_calls:
            # Check if one of the tool calls was for THIS agent
            for tc in last_input_message.tool_calls:
                # Check against raw label, sanitized, or ID
                if tc.get('name') in [self.label, sanitized_name, self.node_id]:
                    is_tool_invocation = True
                    tool_call_id = tc.get('id')
                    # print(f"DEBUG AGENT: Detected Agent '{self.label}' invoked as Tool (ID: {tool_call_id})")
                    break

        if is_tool_invocation and tool_call_id:
             from langchain_core.messages import ToolMessage
             # Return a clean ToolMessage. 
             # We assume the Agent's output content is the "result" of the tool.
             # We strip the "### RESULT FROM" header as it's redundant in a ToolMessage.
             tool_response = ToolMessage(
                 content=str(response.content),
                 tool_call_id=tool_call_id,
                 name=sanitized_name
             )
             return {"messages": [tool_response], "context": context_update, "last_sender": self.node_id}

        from langchain_core.messages import HumanMessage
        
        # Fallback: Standard Agent-to-Agent conversation (HumanMessage)
        final_content = f"### RESULT FROM {self.label} ###\n{response.content}"
        human_response = HumanMessage(content=final_content, name=sanitized_name)
        
        return {"messages": [human_response], "context": context_update, "last_sender": self.node_id}
