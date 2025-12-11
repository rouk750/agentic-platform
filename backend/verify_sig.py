import dspy
import inspect

def test_make_sig():
    try:
        # Proposed structure
        fields = {
            "question": (dspy.InputField, dspy.InputField(desc="The question")),
            "answer": (dspy.OutputField, dspy.OutputField(desc="The answer"))
        }
        
        Sig = dspy.make_signature(
            fields,
            instructions="Answer the question.",
            signature_name="TestSig"
        )
        
        print("Success!")
        print("Input fields:", Sig.input_fields)
        print("Output fields:", Sig.output_fields)
        
    except Exception as e:
        print("Failed with dict:", e)
        # Try finding how to construct it.
        # Maybe just {name: FieldInfo}?
        try:
             fields_simple = {
                "question": dspy.InputField(desc="The question"),
                "answer": dspy.OutputField(desc="The answer")
             }
             Sig2 = dspy.make_signature(
                fields_simple,
                instructions="Answer",
                signature_name="TestSig2"
             )
             print("Success with simple dict!")
        except Exception as e2:
            print("Failed with simple dict:", e2)

if __name__ == "__main__":
    test_make_sig()
