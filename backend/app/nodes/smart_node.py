
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
        for inp in self.inputs:
            key = inp["name"]
            # Try to find key in state (top level) or in last message content?
            if key in state:
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
                print(f"DEBUG SmartNode: Auto-mapped message content to input '{first_input_name}'")
        
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
        if self.mode == "Predict":
            module = dspy.Predict(DynamicSignature)
        else:
            module = dspy.ChainOfThought(DynamicSignature)
            
        # 4.1 Check for Compiled Version and Load
        import os
        compiled_path = f"resources/smart_nodes/{self.node_id}_compiled.json"
        if os.path.exists(compiled_path):
            try:
                module.load(compiled_path)
                # print(f"Loaded compiled module for {self.node_id}")
            except Exception as e:
                print(f"Failed to load compiled module for {self.node_id}: {e}")

            
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
            
        # Return state update. 
        from langchain_core.messages import HumanMessage
        import re
        
        # Create a HumanMessage so the Orchestrator sees it as a distinct result
        # Use sanitized label as name so Orchestrator recognizes who sent it
        sanitized_name = re.sub(r'[^a-zA-Z0-9_-]', '_', self.name)
        
        # Add explicit header
        final_content = f"### RESULT FROM {self.name} ###\n{primary_output_content}"
        human_msg = HumanMessage(content=final_content, name=sanitized_name)
        
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
