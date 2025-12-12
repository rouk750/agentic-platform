
import json
import logging

def make_json_reward(output_keys):
    """
    Creates a reward function that checks if the specified output keys 
    contain valid JSON strings.
    """
    def reward(example, pred, trace=None):
        # logging.info(f"Checking reward for keys: {output_keys}")
        
        all_valid = True
        for key in output_keys:
            # Check if key exists in prediction
            if not hasattr(pred, key):
                # logging.warning(f"Missing key in prediction: {key}")
                return 0.0
                
            val = getattr(pred, key)
            try:
                # Basic cleanup to handle markdown blocks often produced by LLMs
                clean = str(val).strip()
                if clean.startswith("```json"): 
                    clean = clean[7:]
                if clean.endswith("```"): 
                    clean = clean[:-3]
                    
                json.loads(clean.strip())
            except Exception as e:
                # logging.warning(f"Invalid JSON for key '{key}': {e}")
                all_valid = False
                break
        
        return 1.0 if all_valid else 0.0

    return reward

def make_regex_reward(key, pattern):
    """
    Creates a reward function checking if 'key' matches regex 'pattern'.
    """
    import re
    def reward(example, pred, trace=None):
        if not hasattr(pred, key): return 0.0
        val = str(getattr(pred, key)).strip()
        return 1.0 if re.match(pattern, val) else 0.0
    return reward

def make_length_reward(key, max_chars):
    """
    Creates a reward function checking if 'key' length <= max_chars.
    """
    def reward(example, pred, trace=None):
        if not hasattr(pred, key): return 0.0
        val = str(getattr(pred, key))
        return 1.0 if len(val) <= max_chars else 0.0
    return reward

def make_aggregate_reward(rewards):
    """
    Combines multiple reward functions. All must pass (AND logic).
    """
    def reward(example, pred, trace=None):
        for r in rewards:
            if r(example, pred, trace) == 0.0:
                return 0.0
        return 1.0
    return reward
