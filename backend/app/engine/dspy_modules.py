import dspy

class GenericSmartModule(dspy.Module):
    """
    A generic module that wraps a dynamic signature and adds:
    1. ChainOfThought logic
    """
    def __init__(self, signature, mode="ChainOfThought", assertions=None):
        super().__init__()
        self.signature = signature
        # Assertions disabled for DSPy 3.0 compatibility
        
        if mode == "Predict":
            self.predictor = dspy.Predict(signature)
        else:
            self.predictor = dspy.ChainOfThought(signature)
            
    def forward(self, **kwargs):
        # 1. Run Prediction
        pred = self.predictor(**kwargs)
        return pred
# Monkey-patch forward to ensure assertions are active if not using dspy.configure(experimental=True)
# But standard way is to wrap instance.
# We will do it in SmartNode instantiation.

