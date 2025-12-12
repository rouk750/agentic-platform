import os

def is_debug_mode() -> bool:
    """
    Checks if DEBUG_MODE environment variable is set to 'true'.
    """
    return os.getenv("DEBUG_MODE", "false").lower() == "true"

def print_debug(header: str, content: dict):
    """
    Prints a formatted debug block if debug mode is active.
    
    Args:
        header: The title of the debug block (e.g. "DEBUG AGENT Agent_1")
        content: A dictionary of label -> value pairs to print.
    """
    if not is_debug_mode():
        return

    print(f"\n=== [{header}] ===")
    for label, value in content.items():
        print(f"[{label.upper()}] {value}")
    print("=" * (len(header) + 10) + "\n", flush=True)
