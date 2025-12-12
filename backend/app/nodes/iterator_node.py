from typing import Any, Dict, List
import json
from app.engine.state import GraphState

class IteratorNode:
    """
    A deterministic node that iterates over a list of items stored in the GraphState.
    It manages an internal queue within the state context to track progress.
    """
    
    def __init__(self, node_id: str, config: Dict[str, Any]):
        self.node_id = node_id
        self.config = config
        self.label = config.get("label", "Iterator")
        
        # Configuration keys
        self.input_list_variable = config.get("input_list_variable", "items")
        self.output_item_variable = config.get("output_item_variable", "current_item")

    def invoke(self, state: GraphState):
        """
        Executes the iteration logic.
        """
        from app.engine.debug import print_debug
        
        context = state.get("context", {})
        queue_key = f"_iterator_queue_{self.node_id}"
        
        # 1. Initialize Queue if not present
        # 1. Initialize Queue if not present
        total_key = f"_iterator_total_{self.node_id}"
        
        if queue_key not in context:
            source_list = context.get(self.input_list_variable, [])
            
            # Handle stringified JSON if necessary (common with tool outputs)
            if isinstance(source_list, str):
                try:
                    source_list = json.loads(source_list)
                except:
                    print_debug(f"ITERATOR {self.label}", {"Error": f"Failed to parse input list variable '{self.input_list_variable}'"})
                    source_list = []
            
            if not isinstance(source_list, list):
                print_debug(f"ITERATOR {self.label}", {"Error": f"Input variable '{self.input_list_variable}' is not a list. Got {type(source_list)}"})
                source_list = []
                
            # Create a shallow copy to manage the queue safely
            context[queue_key] = list(source_list)
            context[total_key] = len(source_list) # Store total
            print_debug(f"ITERATOR {self.label} [INIT]", {"Queue Size": len(context[queue_key]), "Total": context[total_key]})

        # 2. Process Queue
        queue = context[queue_key]
        total = context.get(total_key, len(queue)) # Fallback if missing
        
        if len(queue) > 0:
            # Pop the next item
            next_item = queue.pop(0)
            
            # Progress Calculation
            # Total 5. Pop 1. Remaining 4. Current = 1. -> 5 - 4 = 1.
            current_index = total - len(queue)
            
            print_debug(f"ITERATOR {self.label} [NEXT]", {"Item": str(next_item)[:100], "Remaining": len(queue), "Progress": f"{current_index}/{total}"})
            
            return {
                # Update context with new queue state and current item
                queue_key: queue, 
                total_key: total, # Persist total
                self.output_item_variable: next_item,
                
                # Signal for the Router/Compiler
                "_signal": "NEXT",
                "last_sender": self.node_id,
                
                # Metadata for Frontend
                "_iterator_metadata": {
                    "node_id": self.node_id,
                    "progress": f"{current_index}/{total}",
                    "current": current_index,
                    "total": total
                }
            }
            
        else:
            # Queue is empty -> Finished
            print_debug(f"ITERATOR {self.label} [COMPLETE]", {"Status": "Done"})
            
            return {
                queue_key: [], # Ensure it stays empty
                total_key: total,
                self.output_item_variable: None, # Optional: clear current item
                "_signal": "COMPLETE",
                "last_sender": self.node_id,
                "_iterator_metadata": {
                    "node_id": self.node_id,
                    "progress": "Done",
                    "current": total,
                    "total": total
                }
            }

    async def __call__(self, state: GraphState):
        return self.invoke(state)
