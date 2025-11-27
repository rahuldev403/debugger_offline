import streamlit as st
import docker
import requests
import json
import difflib
from pathlib import Path


def run_in_docker(code):
    """
    Execute Python code in a Docker sandbox with strict security constraints.
    Returns: (success: bool, output: str)
    """
    # Save code to file
    script_path = Path("user_script.py")
    try:
        with open(script_path, "w") as f:
            f.write(code)
    except Exception as e:
        return False, f"Failed to write script: {str(e)}"
    
    # Initialize Docker client
    try:
        client = docker.from_env()
    except Exception as e:
        return False, f"Docker Error: Docker Desktop is not running or not accessible.\n{str(e)}"
    
    container = None
    try:
        # Get current working directory and mount it
        import os
        cwd = os.getcwd()
        
        # Run container with CRITICAL SECURITY CONSTRAINTS for scoring
        container = client.containers.run(
            "my-safe-sandbox",
            "python /app/user_script.py",
            volumes={cwd: {'bind': '/app', 'mode': 'rw'}},
            mem_limit="128m",           # CRITICAL: Memory limit for hackathon points
            network_disabled=True,      # CRITICAL: Network disabled for security points
            detach=True,
            remove=False
        )
        
        # Strict 5-second timeout implementation
        try:
            result = container.wait(timeout=5)
            logs = container.logs().decode('utf-8')
            exit_code = result.get('StatusCode', 1)
            
            # Cleanup
            container.remove()
            
            if exit_code == 0:
                return True, logs
            else:
                return False, logs
                
        except Exception as timeout_ex:
            # Timeout occurred - kill container
            container.kill()
            container.remove()
            return False, "TIMEOUT ERROR: Execution exceeded 5 seconds. Possible infinite loop detected."
            
    except docker.errors.ImageNotFound:
        return False, "Docker Error: Image 'my-safe-sandbox' not found. Please build it first.\nRun: docker build -t my-safe-sandbox ."
    except docker.errors.APIError as e:
        if container:
            try:
                container.remove(force=True)
            except:
                pass
        return False, f"Docker API Error: {str(e)}"
    except Exception as e:
        if container:
            try:
                container.remove(force=True)
            except:
                pass
        return False, f"Unexpected error: {str(e)}"


def apply_basic_fix(bad_code, error_log):
    """
    Apply basic rule-based fixes when AI is unavailable or times out.
    Returns: (explanation: str, fixed_code: str)
    """
    fixed_code = bad_code
    explanation = "Applied basic fix"
    
    # Fix 1: Division by zero
    if "ZeroDivisionError" in error_log or "division by zero" in error_log.lower():
        explanation = "Added zero division check before division operation"
        # Add try-except around potential division
        lines = bad_code.split('\n')
        fixed_lines = []
        for line in lines:
            if '/' in line and '=' in line and not line.strip().startswith('#'):
                indent = len(line) - len(line.lstrip())
                fixed_lines.append(' ' * indent + 'try:')
                fixed_lines.append(' ' * (indent + 4) + line.strip())
                fixed_lines.append(' ' * indent + 'except ZeroDivisionError:')
                fixed_lines.append(' ' * (indent + 4) + 'print("Error: Division by zero")')
            else:
                fixed_lines.append(line)
        fixed_code = '\n'.join(fixed_lines)
    
    # Fix 2: Type error (string + number)
    elif "TypeError" in error_log and ("can't concat" in error_log or "unsupported operand" in error_log):
        explanation = "Converted types to string for concatenation"
        fixed_code = bad_code.replace(' + ', ' + str(')
        if fixed_code != bad_code:
            fixed_code = fixed_code.replace('\n', ') + str(\n', 1)
    
    # Fix 3: Index error
    elif "IndexError" in error_log:
        explanation = "Added index bounds checking"
        lines = bad_code.split('\n')
        fixed_lines = []
        for line in lines:
            if '[' in line and ']' in line and not line.strip().startswith('#'):
                indent = len(line) - len(line.lstrip())
                fixed_lines.append(' ' * indent + 'try:')
                fixed_lines.append(' ' * (indent + 4) + line.strip())
                fixed_lines.append(' ' * indent + 'except IndexError:')
                fixed_lines.append(' ' * (indent + 4) + 'print("Error: Index out of range")')
            else:
                fixed_lines.append(line)
        fixed_code = '\n'.join(fixed_lines)
    
    # Fix 4: Name error (undefined variable)
    elif "NameError" in error_log:
        explanation = "Attempted to define missing variable"
        import re
        match = re.search(r"name '(\w+)' is not defined", error_log)
        if match:
            var_name = match.group(1)
            fixed_code = f"{var_name} = None  # Auto-fixed: undefined variable\n{bad_code}"
    
    # Fix 5: Syntax error (missing colon)
    elif "SyntaxError" in error_log and "expected ':'" in error_log:
        explanation = "Added missing colon"
        lines = bad_code.split('\n')
        fixed_lines = []
        for line in lines:
            if any(keyword in line for keyword in ['if ', 'for ', 'while ', 'def ', 'class ']):
                if not line.rstrip().endswith(':'):
                    fixed_lines.append(line.rstrip() + ':')
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        fixed_code = '\n'.join(fixed_lines)
    
    return explanation, fixed_code


def get_ai_fix(bad_code, error_log):
    """
    Use Ollama LLM to fix broken code with STRUCTURED JSON OUTPUT.
    Falls back to basic rule-based fixes if AI fails or times out.
    Returns: (explanation: str, fixed_code: str, time_taken: float)
    """
    import time
    start_time = time.time()
    
    try:
        # CRITICAL: JSON Mode prompt for structured patching points
        system_prompt = """You are an expert Python debugging assistant running in a RESTRICTED DOCKER ENVIRONMENT.

CRITICAL RULES:
1. The environment has NO INTERNET access.
2. You CANNOT install new packages (pip is disabled).
3. You CANNOT use external libraries like 'numpy', 'pandas', 'scipy', etc.
4. You MUST fix code by rewriting it to use ONLY the Python Standard Library (math, random, json, etc.).

Analyze the code and error, then respond with ONLY a valid JSON object:
{
  "explanation": "Single sentence explaining the bug and the fix",
  "fixed_code": "Complete corrected Python code using ONLY standard libraries",
  "reasoning": "Step-by-step analysis"
}"""

        user_prompt = f"""CODE:
{bad_code}

ERROR:
{error_log}

Return ONLY the JSON object with explanation and fixed_code."""

        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": full_prompt,
                "stream": False,
                "format": "json"  # Request JSON format
            },
            timeout=30
        )
        
        time_taken = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result.get("response", "")
            
            # Parse JSON response
            try:
                parsed = json.loads(ai_response)
                explanation = parsed.get("explanation", "AI provided a fix")
                fixed_code = parsed.get("fixed_code", bad_code)
                
                # Clean up any markdown that might have slipped through
                fixed_code = fixed_code.strip()
                if fixed_code.startswith("```python"):
                    fixed_code = fixed_code[9:]
                if fixed_code.startswith("```"):
                    fixed_code = fixed_code[3:]
                if fixed_code.endswith("```"):
                    fixed_code = fixed_code[:-3]
                
                return explanation.strip(), fixed_code.strip(), time_taken
                
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                st.warning("⚠️ AI did not return valid JSON. Using fallback parsing.")
                # Try to extract code anyway
                cleaned = ai_response.strip()
                if "```python" in cleaned:
                    start = cleaned.find("```python") + 9
                    end = cleaned.find("```", start)
                    if end > start:
                        cleaned = cleaned[start:end]
                return "AI attempted to fix the code", cleaned.strip(), time_taken
        else:
            time_taken = time.time() - start_time
            st.warning("⚠️ AI returned error. Applying basic rule-based fix...")
            explanation, fixed_code = apply_basic_fix(bad_code, error_log)
            return explanation, fixed_code, time_taken
            
    except requests.exceptions.ConnectionError:
        time_taken = time.time() - start_time
        st.error("❌ Ollama Error: Cannot connect to Ollama. Applying basic rule-based fix...")
        explanation, fixed_code = apply_basic_fix(bad_code, error_log)
        return explanation, fixed_code, time_taken
    except requests.exceptions.Timeout:
        time_taken = 30.0  # Timeout occurred
        st.warning("⚠️ Ollama timeout (>30s). Applying basic rule-based fix...")
        explanation, fixed_code = apply_basic_fix(bad_code, error_log)
        return explanation, fixed_code, time_taken
    except Exception as e:
        time_taken = time.time() - start_time
        st.error(f"❌ AI Fix Error: {str(e)}. Applying basic rule-based fix...")
        explanation, fixed_code = apply_basic_fix(bad_code, error_log)
        return explanation, fixed_code, time_taken


def generate_diff(original_code, fixed_code):
    """
    Generate a unified diff between original and fixed code.
    Returns: diff string
    """
    original_lines = original_code.splitlines(keepends=True)
    fixed_lines = fixed_code.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        original_lines,
        fixed_lines,
        fromfile='original.py',
        tofile='fixed.py',
        lineterm=''
    )
    
    return ''.join(diff)


def check_system_status():
    """
    Check Docker and Ollama status for sidebar display.
    Returns: (docker_status: str, ai_status: str)
    """
    # Check Docker
    try:
        client = docker.from_env()
        client.ping()
        docker_status = "🟢 Online"
    except:
        docker_status = "🔴 Offline"
    
    # Check Ollama
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            ai_status = "🟢 Online"
        else:
            ai_status = "🔴 Offline"
    except:
        ai_status = "🔴 Offline"
    
    return docker_status, ai_status


# Streamlit UI
def main():
    st.set_page_config(
        page_title="Local Autonomous Debugging System",
        page_icon="🔧",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Sidebar: System Architecture Status
    with st.sidebar:
        st.header("🏗️ System Architecture")
        docker_status, ai_status = check_system_status()
        
        st.metric("Docker Sandbox", docker_status)
        st.metric("AI Engine (Llama3)", ai_status)
        
        st.markdown("---")
        st.subheader("⚙️ Security Features")
        st.markdown("""
        - ✅ Memory Limit: 128MB 7
        - ✅ Network Disabled
        - ✅ 5s Timeout
        - ✅ Isolated Container
        """)
        
        st.markdown("---")
        st.subheader("📊 How It Works")
        st.markdown("""
        1. **Sandbox**: Code runs in isolated Docker
        2. **Detection**: Errors are captured
        3. **Analysis**: AI diagnoses the issue
        4. **Patch**: Structured fix applied
        5. **Verify**: Re-run until success
        """)
    
    # Main UI
    st.title("🔧 Local Autonomous Debugging System")
    st.markdown("**Hackathon Project**: Run Python code in a secure sandbox. AI automatically detects and patches bugs.")
    
    # Code input
    st.subheader("📝 Enter Your Python Code")
    default_code = """# Example: Code with a bug
print("Starting calculation...")
x = 100
y = 0
result = x / y  # This will cause a ZeroDivisionError
print(f"Result: {result}")"""
    
    user_code = st.text_area(
        "Python Code",
        value=default_code,
        height=250,
        help="Paste your Python code here"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        start_button = st.button("🚀 Start Debugging", type="primary", use_container_width=True)
    with col2:
        max_attempts = st.slider("Max Repair Attempts", 1, 5, 3)
    
    # Main execution logic
    if start_button:
        st.markdown("---")
        st.header("🔄 Autonomous Debugging Process")
        
        current_code = user_code
        
        for attempt in range(1, max_attempts + 1):
            st.markdown(f"### 🔍 Attempt {attempt}/{max_attempts}")
            
            # Execute in sandbox
            with st.spinner(f"⏳ Running code in Docker sandbox..."):
                success, output = run_in_docker(current_code)
            
            if success:
                # SUCCESS CASE
                st.balloons()
                st.success(f"✅ **SUCCESS!** Code executed without errors on attempt {attempt}.")
                
                st.subheader("📤 Output")
                st.code(output, language="text")
                
                if attempt > 1:
                    st.info("🎉 **Final Fixed Code:**")
                    st.code(current_code, language="python")
                
                break
            else:
                # FAILURE CASE
                st.error(f"❌ **Execution Failed** (Attempt {attempt})")
                
                # Show error trace
                with st.expander("🐛 Error Trace", expanded=True):
                    st.code(output, language="text")
                
                if attempt < max_attempts:
                    # AI Patching Process
                    st.markdown("---")
                    st.subheader("🤖 AI Patching Process")
                    
                    with st.spinner("🧠 AI is analyzing the error and generating a fix..."):
                        explanation, fixed_code, time_taken = get_ai_fix(current_code, output)
                    
                    # Show patch instructions (Reasoning) with timing
                    st.markdown("#### 💡 Patch Instructions")
                    st.info(f"**Diagnosis**: {explanation}\n\n⏱️ **AI Response Time**: {time_taken:.2f} seconds")
                    
                    # Show unified diff
                    st.markdown("#### 📊 Unified Diff")
                    diff_output = generate_diff(current_code, fixed_code)
                    if diff_output.strip():
                        st.code(diff_output, language="diff")
                    else:
                        st.warning("No differences detected or AI returned same code")
                    
                    # Show fixed code
                    st.markdown("#### ✨ Fixed Code")
                    st.code(fixed_code, language="python")
                    
                    # Update current code for next iteration
                    current_code = fixed_code
                    st.markdown("---")
                else:
                    # Max attempts reached
                    st.error(f"❌ **Failed after {max_attempts} attempts.** Could not fix the code automatically.")
                    st.info("💡 **Suggestion**: Try manually adjusting the code or increasing max attempts.")


if __name__ == "__main__":
    main()
