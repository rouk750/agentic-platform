import dspy
import os
import json
from dspy.teleprompt import BootstrapFewShot
from app.schemas.dspy_schema import OptimizationRequest, OptimizationResponse
from app.engine.dspy_utils import get_dspy_lm
from app.models.settings import LLMProfile
from sqlmodel import Session, select

# Directory to save compiled programs
COMPILED_NODES_DIR = "resources/smart_nodes"
os.makedirs(COMPILED_NODES_DIR, exist_ok=True)

class SmartNodeSignature(dspy.Signature):
    # Base class, but we usually build dynamically.
    pass

async def optimize_node(request: OptimizationRequest, session: Session) -> OptimizationResponse:
    # 1. Fetch LLM Profile
    profile = session.get(LLMProfile, request.llm_profile_id)
    if not profile:
        raise ValueError(f"LLM Profile {request.llm_profile_id} not found")
    
    teacher_lm = get_dspy_lm(profile)
    
    # 2. Optimization within Context
    # dspy.settings.configure(...) is not async-safe for concurrent requests.
    # Use context manager instead.
    with dspy.context(lm=teacher_lm):
        
        # Dynamic connection signature
        try:
             # Merge inputs and outputs into a single definition dict
            # format: {name: dspy.InputField or dspy.OutputField}
            signature_fields = {}
            
            for i in request.inputs:
                signature_fields[i["name"]] = dspy.InputField(desc=i.get("desc", ""))
                
            for o in request.outputs:
                signature_fields[o["name"]] = dspy.OutputField(desc=o.get("desc", ""))
            
            DynamicSignature = dspy.make_signature(
                signature_fields,
                instructions=request.goal,
                signature_name=f"Node_{request.node_id}"
            )

            # Create Module to Optimize
            if request.mode == "Predict":
                module = dspy.Predict(DynamicSignature)
            else:
                module = dspy.ChainOfThought(DynamicSignature)

            # Prepare Training Data
            trainset = []
            for ex in request.examples:
                # dspy.Example(input_key=val, output_key=val).with_inputs('input_key')
                d_ex = dspy.Example(**ex.inputs, **ex.outputs).with_inputs(*[i["name"] for i in request.inputs])
                trainset.append(d_ex)

            if not trainset:
                 # Need at least one example to even try "FewShot" usually, 
                 # but BootstrapFewShot needs a trainset to bootstrap from.
                 return OptimizationResponse(status="skipped", compiled_program_path="", score=0.0)

            # Define Metric
            from app.engine.dspy_metrics import llm_metric

            metric_fn = None
            if request.metric in ["semantic", "llm_judge"]:
                metric_fn = llm_metric
            else:
                 # Default exact match
                def validate_answer(example, pred, trace=None):
                    for o in request.outputs:
                        key = o["name"]
                        if getattr(example, key) != getattr(pred, key):
                            return False
                    return True
                metric_fn = validate_answer

            # Run Optimizer (BootstrapFewShot)
            # Run Optimizer (BootstrapFewShot)
            # Uses the same LM for teacher and student for simplicity.
            # Use user-provided max_rounds or fallback to 10
            max_rounds = request.max_rounds if request.max_rounds else 10
            
            # Cap max_rounds at len(trainset) because we can't have more rounds than examples to bootstrap from
            # (DSPy limitation/logic: each round picks a candidate)
            # Actually, DSPy allows max_rounds > len(trainset) but it's redundant if deterministic.
            # Since we bootstrap, randomness is involved, so strict capping isn't strictly necessary but good practice to avoid over-work.
            # Let's trust the user's setting but capped at 50 for safety.
            max_rounds = min(max_rounds, 50) 

            teleprompter = BootstrapFewShot(
                metric=metric_fn, 
                max_bootstrapped_demos=4, 
                max_labeled_demos=8, 
                max_rounds=max_rounds
            )
            
            # Compile!
            compiled_module = teleprompter.compile(module, trainset=trainset)

            # Save
            save_path = os.path.join(COMPILED_NODES_DIR, f"{request.node_id}_compiled.json")
            compiled_module.save(save_path)
            
            return OptimizationResponse(
                status="success",
                compiled_program_path=save_path,
                score=1.0 # Placeholder
            )

        except Exception as e:
            # Re-raise to be caught by api wrapper which prints trace
            raise e
