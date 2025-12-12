import dspy

class Assess(dspy.Signature):
    """Assess the quality of a prediction against an expected answer or goal."""
    
    context = dspy.InputField(desc="The context or input fed to the model")
    prediction = dspy.InputField(desc="The model's actual output")
    expected_answer = dspy.InputField(desc="The expected answer (gold standard)", optional=True)
    assessment_question = dspy.InputField(desc="The criteria to judge the prediction")
    
    assessment_answer = dspy.OutputField(desc="Yes or No")
    # rationale = dspy.OutputField(desc="Why this assessment was given") # CoT implicit with dspy.ChainOfThought for Judge often better

def llm_metric(gold, pred, trace=None):
    """
    A generic semantic metric using a simplified Judge.
    It checks if the prediction semantically matches the gold answer.
    """
    
    # 1. Get the input/context from the example
    # DSPy examples store inputs usually accessible via keys matching the signature.
    # But 'gold' is the Example object.
    
    # We construct a generic question if none provided
    question = "Does the prediction semantically match the expected answer?"
    
    # Prepare Judge Input
    # gold is the Example (contains all inputs + gold outputs)
    # pred is the Prediction (contains all generated outputs)
    
    # We need to extract the main content.
    # Heuristic: Take the first field defined in inputs/outputs?
    # Or just dump the string rep?
    
    # Let's try to find common keys between gold and pred
    # Usually we compare specific keys.
    # For a generic node, we iterate over all expected outputs.
    
    # We define a generic 'semantic_match' over all output fields
    
    # Access expected keys from gold (it behaves like a dict or object)
    # dspy Example is tricky, let's look at dirs
    
    matches = []
    
    # We rely on specific keys being present. 
    # Since this is a generic metric, we iterate over keys present in 'pred' 
    # that are ALSO in 'gold'.
    
    keys_to_compare = [k for k in pred.keys() if k in gold.keys()]
    
    if not keys_to_compare:
        # Fallback or strict fail?
        # Maybe the gold doesn't have the key?
        return False
        
    for key in keys_to_compare:
        expected = gold[key]
        actual = pred[key]
        
        # Simple equality fast-track
        if expected == actual:
            matches.append(True)
            continue
            
        # LLM Judge
        judge = dspy.ChainOfThought(Assess)
        
        # Context is hard to guess generically, maybe just empty or the input keys?
        # Let's stringify inputs from gold
        inputs_dict = {k:v for k,v in gold.items() if k not in pred.keys()}
        context_str = str(inputs_dict)
        
        with dspy.context(lm=dspy.settings.lm): # Use the configured LM (Teacher)
            res = judge(
                context=context_str,
                prediction=str(actual),
                expected_answer=str(expected),
                assessment_question=f"Is the value for '{key}' semantically equivalent to the expected answer?"
            )
            
        # Parse Yes/No
        answer = res.assessment_answer.lower().strip()
        score = "yes" in answer
        matches.append(score)
        
    return all(matches)
