# Test Examples for Self-Healing Code Dashboard
# Copy and paste these into the Streamlit UI to test

# =============================================================================
# Example 1: Simple Division by Zero Error
# =============================================================================
EXAMPLE_1_DIVISION_ERROR = """
print("Starting calculation...")
x = 100
y = 0
result = x / y  # This will fail
print(f"Result: {result}")
"""

# =============================================================================
# Example 2: Type Error (string + int)
# =============================================================================
EXAMPLE_2_TYPE_ERROR = """
name = "Python"
version = 3
message = name + version  # This will fail
print(message)
"""

# =============================================================================
# Example 3: Import Error
# =============================================================================
EXAMPLE_3_IMPORT_ERROR = """
import non_existent_module  # This will fail
print("Hello World")
"""

# =============================================================================
# Example 4: Index Error
# =============================================================================
EXAMPLE_4_INDEX_ERROR = """
numbers = [1, 2, 3, 4, 5]
print("First number:", numbers[0])
print("Last number:", numbers[10])  # This will fail
"""

# =============================================================================
# Example 5: Syntax Error (missing colon)
# =============================================================================
EXAMPLE_5_SYNTAX_ERROR = """
for i in range(5)  # Missing colon
    print(i)
"""

# =============================================================================
# Example 6: Name Error (undefined variable)
# =============================================================================
EXAMPLE_6_NAME_ERROR = """
print("Starting...")
print(undefined_variable)  # This will fail
print("Done")
"""

# =============================================================================
# Example 7: Working Code (should succeed immediately)
# =============================================================================
EXAMPLE_7_WORKING_CODE = """
import math

print("Self-Healing Code Test - Success Case")
print("=" * 50)

# Simple calculations
result = 10 + 20
print(f"Addition: 10 + 20 = {result}")

# Using math module
sqrt_value = math.sqrt(16)
print(f"Square root of 16: {sqrt_value}")

# List operations
numbers = [1, 2, 3, 4, 5]
print(f"Sum of numbers: {sum(numbers)}")

print("=" * 50)
print("All tests passed!")
"""

# =============================================================================
# Example 8: Multiple Errors (chain of problems)
# =============================================================================
EXAMPLE_8_MULTIPLE_ERRORS = """
# This has multiple issues
x = "10"
y = 5
result = x + y  # Type error
print(result)

data = [1, 2, 3]
print(data[5])  # Index error
"""

# =============================================================================
# Example 9: Infinite Loop (will timeout)
# =============================================================================
EXAMPLE_9_TIMEOUT = """
import time

print("Starting infinite loop...")
while True:
    time.sleep(0.1)
    # This will timeout after 5 seconds
"""

# =============================================================================
# Example 10: Complex Logic Error
# =============================================================================
EXAMPLE_10_LOGIC_ERROR = """
def calculate_average(numbers):
    total = sum(numbers)
    count = len(numbers)
    return total / count  # Will fail if empty list

# Test
values = []
avg = calculate_average(values)
print(f"Average: {avg}")
"""


if __name__ == "__main__":
    print("Test Examples for Self-Healing Code Dashboard")
    print("=" * 70)
    print("\nCopy any of these examples into the Streamlit UI:\n")
    
    examples = [
        ("Division by Zero", EXAMPLE_1_DIVISION_ERROR),
        ("Type Error", EXAMPLE_2_TYPE_ERROR),
        ("Import Error", EXAMPLE_3_IMPORT_ERROR),
        ("Index Error", EXAMPLE_4_INDEX_ERROR),
        ("Syntax Error", EXAMPLE_5_SYNTAX_ERROR),
        ("Name Error", EXAMPLE_6_NAME_ERROR),
        ("Working Code", EXAMPLE_7_WORKING_CODE),
        ("Multiple Errors", EXAMPLE_8_MULTIPLE_ERRORS),
        ("Timeout Test", EXAMPLE_9_TIMEOUT),
        ("Logic Error", EXAMPLE_10_LOGIC_ERROR),
    ]
    
    for i, (name, code) in enumerate(examples, 1):
        print(f"\n{i}. {name}")
        print("-" * 70)
        print(code.strip())
        print()
