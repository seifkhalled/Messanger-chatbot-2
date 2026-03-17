
import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from src.fsm.state_machine import apply_fsm, START, ASKED_NAME, ASKED_PHONE, COMPLETED

def test_fsm():
    print("Testing FSM Transitions...")
    
    # 1. New user starts
    next_s, reply, data = apply_fsm(None, "hi")
    print(f"START -> {next_s} | Reply: {reply}")
    assert next_s == ASKED_NAME
    
    # 2. User provides name
    lead = {"state": ASKED_NAME}
    next_s, reply, data = apply_fsm(lead, "John Doe")
    print(f"ASKED_NAME -> {next_s} | Reply: {reply} | Data: {data}")
    assert next_s == ASKED_PHONE
    assert data["name"] == "John Doe"
    
    # 3. User provides phone
    lead = {"state": ASKED_PHONE, "name": "John Doe"}
    next_s, reply, data = apply_fsm(lead, "555-0199")
    print(f"ASKED_PHONE -> {next_s} | Reply: {reply} | Data: {data}")
    assert next_s == COMPLETED
    assert data["phone"] == "555-0199"
    
    # 4. Repeating completion
    lead = {"state": COMPLETED, "name": "John Doe", "phone": "555-0199"}
    next_s, reply, data = apply_fsm(lead, "hello again")
    print(f"COMPLETED -> {next_s} | Reply: {reply}")
    assert next_s == COMPLETED
    
    print("\n✅ FSM Logic Verified!")

if __name__ == "__main__":
    test_fsm()
