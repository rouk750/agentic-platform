
from typing import Any, Dict, List
import dspy
from app.engine.dspy_utils import get_dspy_lm
from app.models.settings import LLMProfile

class SmartNode:
    """
    A Node that uses DSPy to execute 'Smart' logic (Predict or ChainOfThought).
    It dynamically creates a Signature based on inputs/outputs.
    """
    def __init__(self, node_id: str, node_data: Dict[str, Any]):
        self.node_id = node_id
        self.node_data = node_data
        self.name = node_data.get("label", "Smart Node")
        
        # Profile Configuration
        self.profile_config = node_data.get("profile", {}) # Expecting JSON profile or reference
        # For now, we assume the frontend sends the full profile or we look it up.
        # Actually, in other nodes (GenericAgentNode), we might look it up.
        # Here we assume the Runner/Compiler passes initialized stuff or we handle it efficiently.
        # Let's assume passed profile data for now.
        
        # Configuration
        self.mode = node_data.get("mode", "ChainOfThought") # Or "Predict"
        self.inputs = node_data.get("inputs", [{"name": "input", "desc": "Input text"}])
        self.outputs = node_data.get("outputs", [{"name": "output", "desc": "Output text"}])
        self.goal = node_data.get("goal", "Process the input.")
        
    async def invoke(self, state: Dict[str, Any]):
        # 1. Prepare Inputs
        # The 'state' typically contains 'messages' or 'keys'.
        # We need to map state to signature inputs.
        # Convention: usage of state[key] if key matches input name.
        
        dspy_inputs = {}
        context = state.get("context", {})
        
        for inp in self.inputs:
            key = inp["name"]
            # 1. Try Shared Context (Blackboard) - Priority for variables
            if key in context:
                dspy_inputs[key] = context[key]
            # 2. Try Top-level State (rarely used for vars, but maybe for direct inputs)
            elif key in state:
                dspy_inputs[key] = state[key]
        
        # Fallback: If we have not found inputs yet, and we have messages,
        # assign the last message content to the FIRST input field.
        # This allows "piping" conversation text into the SmartNode without matching exact key names.
        messages = state.get("messages", [])
        if not dspy_inputs and self.inputs and messages:
            last_msg_content = messages[-1].content
            
            # 1. Try unpacking JSON content (Orchestrator style)
            mapped = False
            try:
                import json
                # Handle possible list or dict structure from Orchestrator
                if isinstance(last_msg_content, str):
                    clean_json = last_msg_content.strip()
                    if clean_json.startswith("```json"): clean_json = clean_json[7:]
                    if clean_json.endswith("```"): clean_json = clean_json[:-3]
                    
                    data = json.loads(clean_json)
                    
                    # Unpack 'params' if present (Orchestrator format: {"agent":..., "params": [...]})
                    source_data = data
                    if isinstance(data, dict) and "params" in data:
                        params = data["params"]
                        if isinstance(params, list) and len(params) > 0:
                            # Case A: [{"key": "value"}] - List of Dicts
                            if isinstance(params[0], dict):
                                source_data = params[0]
                            # Case B: ["value"] - List of Values (Positional)
                            else:
                                for i, val in enumerate(params):
                                    if i < len(self.inputs):
                                        dspy_inputs[self.inputs[i]["name"]] = val
                                        mapped = True
                                source_data = {} # Already mapped
                        elif isinstance(params, dict):
                            source_data = params
                            
                    # Map keys to inputs (Named params)
                    if isinstance(source_data, dict):
                        for inp in self.inputs:
                            if inp["name"] in source_data:
                                dspy_inputs[inp["name"]] = source_data[inp["name"]]
                                mapped = True
            except:
                pass
            
            # 2. Fallback: Auto-map raw content if no JSON mapping succeeded
            if not mapped:
                first_input_name = self.inputs[0]["name"]
                dspy_inputs[first_input_name] = last_msg_content

        
        if not dspy_inputs and self.inputs:
             return {"error": f"Missing inputs for {self.name}. Expected { [i['name'] for i in self.inputs] }"}

        # 2. Setup LM
        # We need to reconstruct the profile object
        profile_data = self.node_data.get("llm_profile")
        if not profile_data:
             # Fallback default or error
             return {"error": "No LLM Profile configured for Smart Node"}
             
        profile = LLMProfile(**profile_data)
        dspy_lm = get_dspy_lm(profile)
        
        # 3. Dynamic Signature
        # dspy.make_signature(signature_name, instructions, input_fields, output_fields)
        # input_fields/output_fields are dicts or tuples
        
        signature_fields = {}
        for i in self.inputs:
            signature_fields[i["name"]] = dspy.InputField(desc=i.get("desc", ""))
        for o in self.outputs:
            signature_fields[o["name"]] = dspy.OutputField(desc=o.get("desc", ""))
        
        DynamicSignature = dspy.make_signature(
            signature_fields,
            instructions=self.goal,
            signature_name=f"Node_{self.node_id}"
        )
        
        # 4. Create Module
        # 4. Create Module
        if self.mode == "Predict":
            module = dspy.Predict(DynamicSignature)
        else:
            module = dspy.ChainOfThought(DynamicSignature)
            
        # 4b. Apply Guardrails via Refine (Explicit Configuration)
        json_keys = []
        has_guardrails = False
        
        for o in self.outputs:
            # Check explicit flag 'force_json' (Legacy) OR new 'guardrail' config
            guardrail = o.get("guardrail", {})
            if guardrail is None: guardrail = {}
            
            # JSON Check
            if o.get("force_json") is True or guardrail.get("id") == "json":
                json_keys.append(o["name"])
                has_guardrails = True
            
            # Check other guardrails existence
            if guardrail.get("id") in ["regex", "length"]:
                has_guardrails = True
        
        if has_guardrails:
            rewards = []
            # Import aggregate and legacy json reward (still useful for global check if needed, 
            # though we could technically move JSON to the loop too, effectively treating it per-field)
            from app.engine.dspy_rewards import make_aggregate_reward, make_json_reward
            from app.services.guardrail_registry import get_guardrail_factory

            # 1. Legacy/Global JSON Check
            # We enforce this if 'json_keys' list is populated (from force_json legacy or guardrail='json')
            if json_keys:
                rewards.append(make_json_reward(json_keys))
                
            # 2. Dynamic Guardrails Loop
            for o in self.outputs:
                # Support new list format 'guardrails' AND legacy single object 'guardrail'
                g_list = o.get("guardrails", [])
                if isinstance(o.get("guardrail"), dict):
                    g_list.append(o["guardrail"])
                
                for guardrail in g_list:
                    if not guardrail: continue
                    
                    gid = guardrail.get("id")
                    if gid == "json": continue 
                    
                    factory = get_guardrail_factory(gid)
                    if factory:
                        params = guardrail.get("params", {})
                        try:
                           if gid == "length" and "max_chars" in params:
                               params["max_chars"] = int(params["max_chars"])
                               
                           reward_fn = factory(o["name"], **params)
                           rewards.append(reward_fn)
                        except Exception as e:
                            print(f"Failed to instantiate guardrail {gid} for {o['name']}: {e}")

            # Wrap with Refine if we have ANY rewards
            if rewards:
                module = dspy.Refine(
                    module=module,
                    N=3,
                    reward_fn=make_aggregate_reward(rewards),
                    threshold=1.0
                )

        # 4.1 Check for Compiled Version and Load
        # IMPT: We must load state into the INNER module if we wrapped it, 
        # or load into the refine module? 
        # Usually Refine wraps a module. If we compiled the inner module, we should load it there.
        # But if we compiled the Refine module (unlikely), we load it on top.
        # Let's assume we load into the base module (inner) for now.
        
        target_load_module = module
        if isinstance(module, dspy.Refine):
             # Access internal module? dspy.Refine store it as self.module 
             # (based on signature inspection or standard wrapping)
             if hasattr(module, 'module'):
                 target_load_module = module.module
        
        import os
        compiled_path = f"resources/smart_nodes/{self.node_id}_compiled.json"
        
        if os.path.exists(compiled_path):
            try:
                target_load_module.load(compiled_path)
                # print(f"Loaded compiled module for {self.node_id}")
            except Exception as e:
                print(f"WARNING: Failed to load compiled module for {self.node_id} (Version Mismatch?): {e}")
                print("Continuing with un-optimized module (Zero-Shot).")
                # Do not re-raise, allow fallback to zero-shot execution


            
        # 5. Execute
        # We use 'with dspy.context(lm=dspy_lm):'
        # DSPy is synchronous by default usually, but dspy-ai 3.x is async friendly?
        # dspy 2.5 uses `forward`.
        # We should check if we need to run in executor if it's blocking.
        # For now assume sync call is acceptable or wrap it.
        
        from app.engine.debug import print_debug
        
        with dspy.context(lm=dspy_lm):
            debug_inputs = dspy_inputs
            debug_result = "Exec Failed"
            
            try:
                result = module(**dspy_inputs)
                # DSPy 2.4/2.5 Prediction object can crash on __repr__ if empty
                try:
                    debug_result = str(result)
                except Exception:
                     debug_result = "<Empty or Invalid Prediction Object>"
            except Exception as e:
                print(f"DSPy Module Execution failed: {e}")
                raise e
            finally:
                print_debug(f"DEBUG SMART NODE {self.name} ({self.node_id})", {
                    "Inputs": debug_inputs,
                    "Result": debug_result
                })
            
        # 6. Map Outputs
        outputs = {}
        primary_output_content = ""
        
        # Check if result is valid
        if result is None:
             return {"error": "SmartNode produced no result (None)."}
        
        for out in self.outputs:
            key = out["name"]
            # Accessing attribute on Prediction might also trigger the iteration if it's dynamic
            # In DSPy, result.key usually accesses completions.
            try:
                if hasattr(result, key):
                    val = getattr(result, key)
                    outputs[key] = val
                    # Heuristic: The first output or one named 'output' is the primary content
                    if not primary_output_content:
                        primary_output_content = str(val)
                    elif key == "output":
                         primary_output_content = str(val)
            except Exception as e:
                 print(f"Failed to extract output '{key}': {e}")

        if not outputs:
             return {"error": "SmartNode produced no valid outputs processing the LM response."}
                
        # Optional: Add rationale if ChainOfThought
        if hasattr(result, "rationale"):
             try:
                outputs["_rationale"] = result.rationale
             except:
                 pass
            
        # 7. Extract Token Usage from DSPy History
        usage_metadata = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        debug_history_dump = {}

        def _extract_from_obj(u):
            """Helper to extract usage from a dict or object"""
            i = 0
            o = 0
            t = 0
            # Try dict access
            if isinstance(u, dict):
                i = u.get("prompt_tokens") or u.get("input_tokens") or 0
                o = u.get("completion_tokens") or u.get("output_tokens") or 0
                t = u.get("total_tokens") or 0
            # Try object attributes
            else:
                i = getattr(u, "prompt_tokens", 0) or getattr(u, "input_tokens", 0)
                o = getattr(u, "completion_tokens", 0) or getattr(u, "output_tokens", 0)
                t = getattr(u, "total_tokens", 0)
            return i, o, t

        try:
            if hasattr(dspy_lm, "history") and dspy_lm.history:
                if len(dspy_lm.history) > 0:
                    last = dspy_lm.history[-1]
                    debug_history_dump["last_keys"] = list(last.keys())
                    
                    # Capture kwargs
                    if "kwargs" in last:
                        debug_history_dump["kwargs_keys"] = list(last["kwargs"].keys())
                        debug_history_dump["kwargs_repr"] = str(last["kwargs"])

                    if "usage" in last:
                        debug_history_dump["top_usage_repr"] = str(last["usage"])
                    
                    if "response" in last:
                        r = last["response"]
                        debug_history_dump["resp_type"] = str(type(r))
                        
                        # Try to invoke to_dict or dict() or vars()
                        try:
                            if hasattr(r, "model_dump"):
                                debug_history_dump["resp_model_dump"] = r.model_dump()
                            elif hasattr(r, "dict"):
                                debug_history_dump["resp_dict"] = r.dict()
                            else:
                                debug_history_dump["resp_vars"] = str(vars(r))
                        except Exception as e:
                            debug_history_dump["resp_dump_error"] = str(e)

                        if hasattr(r, "usage"):
                             debug_history_dump["resp_usage_repr"] = str(r.usage)
                        elif isinstance(r, dict) and "usage" in r:
                             debug_history_dump["resp_usage_dict"] = str(r["usage"])

                for interaction in dspy_lm.history:
                    # Generic extraction
                    i, o, t = 0, 0, 0
                    
                    # 1. Try top-level usage
                    if "usage" in interaction and interaction["usage"]:
                         ti, to, tt = _extract_from_obj(interaction["usage"])
                         if ti + to + tt > 0:
                             usage_metadata["input_tokens"] += ti
                             usage_metadata["output_tokens"] += to
                             usage_metadata["total_tokens"] += tt
                             continue # Skip response check if we found it here
                    
                if "response" in interaction:
                        resp = interaction["response"]
                        u_cand = None
                        if isinstance(resp, dict):
                            u_cand = resp.get("usage")
                        elif hasattr(resp, "usage"):
                            u_cand = resp.usage
                        
                        if u_cand:
                             ti, to, tt = _extract_from_obj(u_cand)
                             usage_metadata["input_tokens"] += ti
                             usage_metadata["output_tokens"] += to
                             usage_metadata["total_tokens"] += tt
                
                # 3. FALLBACK: Manual Calculation if Usage is 0 (Common with some Providers/Ollama via LiteLLM)
                if usage_metadata["total_tokens"] == 0:
                    # Heuristic: 1 token ~= 4 chars
                    # We iterate history to approximate inputs and outputs.
                    est_input = 0
                    est_output = 0
                    
                    for interaction in dspy_lm.history:
                         # Inputs
                         if "messages" in interaction:
                             # sum content of messages
                             for m in interaction["messages"]:
                                 c = m.get("content", "")
                                 est_input += len(str(c))
                         elif "prompt" in interaction:
                             est_input += len(str(interaction["prompt"]))
                         
                         # Outputs
                         if "response" in interaction:
                             # Try to get choices
                             r = interaction["response"]
                             content = ""
                             # Standard Litellm/OpenAI structure
                             if hasattr(r, "choices") and r.choices:
                                 content = r.choices[0].message.content
                             elif isinstance(r, dict) and "choices" in r:
                                 content = r["choices"][0]["message"]["content"]
                             
                             est_output += len(str(content))
                    
                    usage_metadata["input_tokens"] = est_input // 4
                    usage_metadata["output_tokens"] = est_output // 4
                    usage_metadata["total_tokens"] = usage_metadata["input_tokens"] + usage_metadata["output_tokens"]
                    
        except Exception:
            pass
            
        
        # Return state update. 
        from langchain_core.messages import HumanMessage
        import re
        
        # Create a HumanMessage so the Orchestrator sees it as a distinct result
        # Use sanitized label as name so Orchestrator recognizes who sent it
        sanitized_name = re.sub(r'[^a-zA-Z0-9_-]', '_', self.name)
        
        # Add explicit header
        final_content = f"### RESULT FROM {self.name} ###\n{primary_output_content}"
        
        additional_kwargs = {"usage_metadata": usage_metadata, "_dspy_debug": debug_history_dump}

        # Attach usage metadata (Standard LangChain Core 0.2+)
        try:
             human_msg = HumanMessage(
                 content=final_content, 
                 name=sanitized_name,
                 usage_metadata=usage_metadata,
                 additional_kwargs=additional_kwargs
             )
        except Exception:
             # Fallback for older versions
             human_msg = HumanMessage(
                 content=final_content, 
                 name=sanitized_name,
                 additional_kwargs=additional_kwargs
             )
        
        # SmartNode is generic -> it updates keys in state AND appends a message
        return {**outputs, "messages": [human_msg], "last_sender": self.node_id}

    async def __call__(self, state):
        try:
            return await self.invoke(state)
        except RuntimeError as e:
            if "StopIteration" in str(e):
                 # This captures the coroutine StopIteration specifically
                 return {"error": "DSPy failed to generate a prediction (Empty response from LLM). Check your model configuration."}
            raise e
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"error": f"SmartNode execution failed: {e}"}
