
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
            else:
                # Fallback: if single input, use "input" from state messages usually
                # For Agentic Platform, users might map explicitly. 
                # Simplification: If 1 input and input name is 'input', take last human message.
                messages = state.get("messages", [])
                if key == "input" and messages:
                    dspy_inputs[key] = messages[-1].content
        
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
        
        with dspy.context(lm=dspy_lm):
            result = module(**dspy_inputs)
            
        # 6. Map Outputs
        outputs = {}
        for out in self.outputs:
            key = out["name"]
            if hasattr(result, key):
                outputs[key] = getattr(result, key)
                
        # Optional: Add rationale if ChainOfThought
        if hasattr(result, "rationale"):
            outputs["_rationale"] = result.rationale
            
        # Return state update. 
        # Usually we update a specific key or append a message.
        # SmartNode is generic -> it updates keys in state.
        return outputs

    def __call__(self, state):
        import asyncio
        return asyncio.run(self.invoke(state)) # LangGraph expects sync usually unless async node
