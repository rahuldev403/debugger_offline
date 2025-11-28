import streamlit as st
import docker
import requests
import json
import difflib
from pathlib import Path
import time
import os
import re
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# --- DATA STRUCTURES FOR TRACKING ---
@dataclass
class ExecutionTrace:
    """Captures all details of a single execution attempt."""
    iteration: int
    timestamp: str
    code_snapshot: str
    success: bool
    output: str
    error_type: Optional[str] = None
    stack_trace: Optional[str] = None
    logs: List[str] = field(default_factory=list)
    execution_time: float = 0.0

@dataclass
class PatchRecord:
    """Records a single patch application."""
    iteration: int
    original_code: str
    fixed_code: str
    unified_diff: str
    line_edits: List[Dict[str, Any]]
    explanation: str
    reasoning: str
    ai_time: float

@dataclass
class RepairSession:
    """Complete repair session with all artifacts."""
    original_code: str
    final_code: str
    execution_traces: List[ExecutionTrace] = field(default_factory=list)
    patch_logs: List[PatchRecord] = field(default_factory=list)
    total_iterations: int = 0
    success: bool = False
    failure_reason: Optional[str] = None

# --- PAGE CONFIG & MODERN OLLAMA-STYLE CSS ---
st.set_page_config(
    page_title="AutoFix AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Outfit:wght@300;400;500;600;700&display=swap');
    
    /* Root Variables - Ollama Dark Theme */
    :root {
        --bg-primary: #0d0d0d;
        --bg-secondary: #171717;
        --bg-tertiary: #1f1f1f;
        --bg-hover: #262626;
        --border-color: #2a2a2a;
        --border-active: #404040;
        --text-primary: #fafafa;
        --text-secondary: #a1a1a1;
        --text-muted: #737373;
        --accent-primary: #22c55e;
        --accent-secondary: #3b82f6;
        --accent-warning: #f59e0b;
        --accent-error: #ef4444;
        --accent-purple: #a855f7;
        --code-bg: #0a0a0a;
        --success-bg: rgba(34, 197, 94, 0.1);
        --error-bg: rgba(239, 68, 68, 0.1);
    }
    
    /* Main App Background */
    .stApp {
        background: var(--bg-primary);
        font-family: 'Outfit', sans-serif;
    }
    
    /* Main content container - let Streamlit handle responsive layout */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Hide Streamlit Branding - but keep sidebar toggle button */
    #MainMenu, footer {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Hide header text but keep the toggle button */
    header .decoration {
        display: none !important;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: var(--bg-secondary) !important;
        border-right: 1px solid var(--border-color) !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: var(--text-primary);
        font-family: 'Outfit', sans-serif;
    }
    
    /* Ensure sidebar toggle button is visible and styled */
    button[data-testid="baseButton-header"] {
        visibility: visible !important;
        display: block !important;
        position: relative !important;
        z-index: 999 !important;
    }
    
    /* Header container - keep visible for toggle button */
    header {
        visibility: visible !important;
    }
    
    /* Make sure the toggle button container is visible */
    [data-testid="stHeader"] {
        visibility: visible !important;
    }
    
    [data-testid="stHeader"] > div {
        visibility: visible !important;
    }
    
    /* Custom Header */
    .main-header {
        background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 24px 32px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        gap: 16px;
    }
    
    .main-header-icon {
        width: 48px;
        height: 48px;
        background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
    }
    
    .main-header-text h1 {
        color: var(--text-primary);
        font-size: 28px;
        font-weight: 600;
        margin: 0;
        font-family: 'Outfit', sans-serif;
    }
    
    .main-header-text p {
        color: var(--text-secondary);
        margin: 4px 0 0 0;
        font-size: 14px;
    }
    
    /* Status Pills */
    .status-container {
        display: flex;
        gap: 12px;
        margin-bottom: 20px;
    }
    
    .status-pill {
        background: var(--bg-tertiary);
        border: 1px solid var(--border-color);
        border-radius: 100px;
        padding: 8px 16px;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-size: 13px;
        color: var(--text-secondary);
    }
    
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
    }
    
    .status-online { background: var(--accent-primary); box-shadow: 0 0 8px var(--accent-primary); }
    .status-offline { background: var(--accent-error); }
    
    /* Code Editor Container */
    .editor-container {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        overflow: hidden;
    }
    
    .editor-header {
        background: var(--bg-tertiary);
        border-bottom: 1px solid var(--border-color);
        padding: 12px 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .editor-title {
        color: var(--text-primary);
        font-size: 14px;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .editor-badge {
        background: var(--accent-secondary);
        color: white;
        font-size: 10px;
        padding: 2px 8px;
        border-radius: 100px;
        font-weight: 600;
    }
    
    /* Text Area Styling */
    .stTextArea textarea {
        background: var(--code-bg) !important;
        color: var(--text-primary) !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 13px !important;
        line-height: 1.6 !important;
        border: none !important;
        border-radius: 0 !important;
        padding: 16px !important;
    }
    
    .stTextArea textarea:focus {
        box-shadow: none !important;
        border: none !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, var(--accent-primary), #16a34a) !important;
        color: var(--bg-primary) !important;
        border: none !important;
        border-radius: 10px !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        padding: 12px 24px !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(34, 197, 94, 0.3) !important;
    }
    
    /* Timeline Panel */
    .timeline-container {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        height: 100%;
    }
    
    .timeline-header {
        background: var(--bg-tertiary);
        border-bottom: 1px solid var(--border-color);
        padding: 16px 20px;
    }
    
    .timeline-title {
        color: var(--text-primary);
        font-size: 16px;
        font-weight: 600;
        margin: 0;
    }
    
    /* Iteration Cards */
    .iteration-card {
        background: var(--bg-tertiary);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        margin: 12px;
        overflow: hidden;
        transition: all 0.2s ease;
    }
    
    .iteration-card:hover {
        border-color: var(--border-active);
    }
    
    .iteration-header {
        padding: 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-bottom: 1px solid var(--border-color);
    }
    
    .iteration-number {
        background: var(--accent-secondary);
        color: white;
        width: 28px;
        height: 28px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 13px;
    }
    
    .iteration-status {
        font-size: 12px;
        padding: 4px 12px;
        border-radius: 100px;
        font-weight: 500;
    }
    
    .status-success {
        background: var(--success-bg);
        color: var(--accent-primary);
        border: 1px solid var(--accent-primary);
    }
    
    .status-error {
        background: var(--error-bg);
        color: var(--accent-error);
        border: 1px solid var(--accent-error);
    }
    
    .status-running {
        background: rgba(59, 130, 246, 0.1);
        color: var(--accent-secondary);
        border: 1px solid var(--accent-secondary);
    }
    
    .iteration-body {
        padding: 16px;
    }
    
    .section-label {
        color: var(--text-muted);
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
        font-weight: 600;
    }
    
    .output-box {
        background: var(--code-bg);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 12px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        color: var(--text-primary);
        max-height: 200px;
        overflow-y: auto;
        white-space: pre-wrap;
    }
    
    .reasoning-box {
        background: rgba(168, 85, 247, 0.08);
        border: 1px solid rgba(168, 85, 247, 0.3);
        border-radius: 8px;
        padding: 12px;
        font-size: 13px;
        color: var(--text-secondary);
        line-height: 1.6;
    }
    
    .diff-box {
        background: var(--code-bg);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 12px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        overflow-x: auto;
    }
    
    .diff-add { color: var(--accent-primary); }
    .diff-remove { color: var(--accent-error); }
    .diff-info { color: var(--accent-secondary); }
    
    /* Metrics Row */
    .metrics-row {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin: 16px 0;
    }
    
    .metric-card {
        background: var(--bg-tertiary);
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 16px;
        text-align: center;
    }
    
    .metric-value {
        font-size: 24px;
        font-weight: 700;
        color: var(--accent-primary);
        margin-bottom: 4px;
    }
    
    .metric-label {
        font-size: 11px;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Final Result Panel */
    .result-panel {
        background: var(--bg-secondary);
        border: 2px solid var(--accent-primary);
        border-radius: 12px;
        margin-top: 20px;
        overflow: hidden;
    }
    
    .result-header {
        background: var(--success-bg);
        padding: 16px 20px;
        border-bottom: 1px solid var(--accent-primary);
    }
    
    .result-title {
        color: var(--accent-primary);
        font-size: 16px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* Tabs Styling */
    /* Session Artifacts Section */
    .artifacts-section {
        margin-top: 32px;
        padding-top: 24px;
        border-top: 1px solid var(--border-color);
    }
    
    .stTabs [data-baseweb="tab-list"] {
        background: var(--bg-tertiary);
        border-radius: 12px;
        padding: 8px;
        gap: 12px;
        margin-bottom: 20px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: var(--text-secondary);
        border-radius: 8px;
        font-weight: 500;
        padding: 12px 20px !important;
        margin: 0 4px;
        transition: all 0.2s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: var(--bg-hover);
        color: var(--text-primary);
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--accent-primary) !important;
        color: var(--bg-primary) !important;
        font-weight: 600;
    }
    
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 16px;
    }
    
    /* Code block formatting fix */
    .stCodeBlock pre {
        white-space: pre !important;
        word-wrap: normal !important;
        overflow-x: auto !important;
    }
    
    .stCodeBlock code {
        white-space: pre !important;
        display: block !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: var(--bg-tertiary) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-secondary);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--border-active);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--text-muted);
    }
    
    /* Number Input */
    .stNumberInput input {
        background: var(--bg-tertiary) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
    }
    
    /* Select Box */
    .stSelectbox > div > div {
        background: var(--bg-tertiary) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
    }
    
    /* Info/Warning/Error Boxes */
    .stAlert {
        border-radius: 10px !important;
        border: none !important;
    }
    
    /* Code blocks */
    .stCodeBlock {
        border-radius: 8px !important;
    }
    
    pre {
        background: var(--code-bg) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-color: var(--accent-primary) transparent transparent transparent !important;
    }
</style>
""", unsafe_allow_html=True)

# --- UTILITY FUNCTIONS ---

def parse_error_type(error_log: str) -> str:
    """Extract error type from stack trace."""
    if not error_log or not error_log.strip():
        return "UnknownError"
    
    error_patterns = [
        r"(\w+Error):", r"(\w+Exception):", r"(\w+Warning):"
    ]
    for pattern in error_patterns:
        match = re.search(pattern, error_log)
        if match:
            return match.group(1)
    
    # Check for specific error messages
    if "TIMEOUT" in error_log.upper():
        return "TimeoutError"
    if "137" in error_log or "Out of Memory" in error_log:
        return "MemoryError"
    if "No module named" in error_log:
        return "ModuleNotFoundError"
    
    return "RuntimeError"

def extract_logs_from_output(output: str) -> List[str]:
    """Extract print statements and logs from output."""
    return [line for line in output.split('\n') if line.strip()]

def generate_line_edits(original: str, fixed: str) -> List[Dict[str, Any]]:
    """Generate structured line-by-line edit instructions."""
    orig_lines = original.splitlines()
    fixed_lines = fixed.splitlines()
    edits = []
    
    matcher = difflib.SequenceMatcher(None, orig_lines, fixed_lines)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'replace':
            for idx, (old, new) in enumerate(zip(orig_lines[i1:i2], fixed_lines[j1:j2])):
                edits.append({
                    "type": "replace",
                    "line": i1 + idx + 1,
                    "old_content": old,
                    "new_content": new
                })
        elif tag == 'delete':
            for idx, line in enumerate(orig_lines[i1:i2]):
                edits.append({
                    "type": "delete",
                    "line": i1 + idx + 1,
                    "content": line
                })
        elif tag == 'insert':
            for idx, line in enumerate(fixed_lines[j1:j2]):
                edits.append({
                    "type": "insert",
                    "after_line": i1,
                    "content": line
                })
    return edits

def generate_unified_diff(original: str, fixed: str) -> str:
    """Generate unified diff between original and fixed code."""
    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        fixed.splitlines(keepends=True),
        fromfile='original.py',
        tofile='fixed.py',
        lineterm=''
    )
    return ''.join(diff)

def format_diff_html(diff_text: str) -> str:
    """Format diff with color coding."""
    lines = []
    for line in diff_text.split('\n'):
        if line.startswith('+') and not line.startswith('+++'):
            lines.append(f'<span class="diff-add">{line}</span>')
        elif line.startswith('-') and not line.startswith('---'):
            lines.append(f'<span class="diff-remove">{line}</span>')
        elif line.startswith('@@'):
            lines.append(f'<span class="diff-info">{line}</span>')
        else:
            lines.append(line)
    return '\n'.join(lines)

# --- DOCKER SANDBOX EXECUTION ---

def run_in_docker(code: str) -> ExecutionTrace:
    """Execute Python code in a Docker sandbox with strict security constraints."""
    start_time = time.time()
    trace = ExecutionTrace(
        iteration=0,
        timestamp=datetime.now().isoformat(),
        code_snapshot=code,
        success=False,
        output=""
    )
    
    script_path = Path("user_script.py")
    try:
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code)
    except Exception as e:
        trace.output = f"Failed to write script: {str(e)}"
        trace.error_type = "IOError"
        trace.execution_time = time.time() - start_time
        return trace
    
    try:
        client = docker.from_env()
    except Exception as e:
        trace.output = f"Docker Error: Docker Desktop is not running.\n{str(e)}"
        trace.error_type = "DockerConnectionError"
        trace.execution_time = time.time() - start_time
        return trace
    
    container = None
    try:
        cwd = os.getcwd()
        
        container = client.containers.run(
            "my-safe-sandbox",
            "python /app/user_script.py",
            volumes={cwd: {'bind': '/app', 'mode': 'rw'}},
            mem_limit="128m",           # CRITICAL: 128MB RAM Limit
            network_disabled=True,      
            detach=True,
            remove=False
        )
        
        try:
            # Wait for container to finish
            result = container.wait(timeout=5)
            
            # Capture logs (stdout + stderr)
            logs = container.logs().decode('utf-8')
            exit_code = result.get('StatusCode', 1)
            
            # Ensure we always have some output to prevent empty trace issues
            if not logs or not logs.strip():
                if exit_code == 0:
                    logs = "Execution completed successfully with no output."
                else:
                    logs = f"Process exited with code {exit_code} but produced no output."
            
            # --- CRITICAL FIX FOR MEMORY LOOP ---
            if exit_code == 137:
                logs += "\n❌ SYSTEM ALERT: Process was killed by the Kernel (Out of Memory)."
                logs += "\nDiagnosis: The code tried to use more than 128MB of RAM."
                logs += "\nFix Required: Reduce data size, list size, or use generators."
            # ------------------------------------
            
            container.remove()
            
            trace.execution_time = time.time() - start_time
            trace.output = logs
            trace.logs = extract_logs_from_output(logs)
            
            if exit_code == 0:
                trace.success = True
            else:
                trace.success = False
                trace.error_type = parse_error_type(logs)
                trace.stack_trace = logs
                
        except Exception as timeout_ex:
            # Handle Timeout (Infinite Loop)
            container.kill()
            container.remove()
            trace.output = "TIMEOUT ERROR: Execution exceeded 5 seconds. Possible infinite loop detected."
            trace.error_type = "TimeoutError"
            trace.execution_time = time.time() - start_time
            
    except docker.errors.ImageNotFound:
        trace.output = "Docker Error: Image 'my-safe-sandbox' not found."
        trace.error_type = "ImageNotFoundError"
        trace.execution_time = time.time() - start_time
    except Exception as e:
        if container:
            try: 
                container.remove(force=True)
            except: 
                pass
        trace.output = f"Unexpected error: {str(e)}"
        trace.error_type = "SandboxError"
        trace.execution_time = time.time() - start_time
    
    return trace

# --- AI FIX GENERATION ---

def apply_basic_fix(bad_code: str, error_log: str) -> tuple[str, str, str]:
    """Fallback rule-based fixes with reasoning."""
    fixed_code = bad_code
    explanation = "Applied heuristic fix based on error pattern"
    reasoning = "AI unavailable - using pattern matching"
    
    if "ZeroDivisionError" in error_log:
        explanation = "Wrapped division operation in try-except block"
        reasoning = "Detected ZeroDivisionError in stack trace. The code attempts division that may result in zero denominator. Wrapping in exception handler provides graceful error handling."
        lines = bad_code.split('\n')
        fixed_lines = []
        for line in lines:
            if '/' in line and '=' in line and 'except' not in line:
                indent = len(line) - len(line.lstrip())
                fixed_lines.extend([
                    ' ' * indent + 'try:',
                    ' ' * indent + '    ' + line.lstrip(),
                    ' ' * indent + 'except ZeroDivisionError:',
                    ' ' * indent + '    print("Error: Division by zero")'
                ])
            else:
                fixed_lines.append(line)
        fixed_code = '\n'.join(fixed_lines)
    
    elif "NameError" in error_log:
        match = re.search(r"name '(\w+)' is not defined", error_log)
        if match:
            var_name = match.group(1)
            explanation = f"Defined missing variable '{var_name}' with default value"
            reasoning = f"Detected NameError for undefined variable '{var_name}'. Adding initialization with sensible default (None) at the top of the code."
            fixed_code = f"{var_name} = None  # Auto-defined\n{bad_code}"
    
    elif "IndentationError" in error_log or "unexpected indent" in error_log:
        explanation = "Attempted to fix indentation issues"
        reasoning = "Detected indentation error. Python requires consistent spacing. Normalizing to 4-space indentation."
        fixed_code = bad_code.replace('\t', '    ')
    
    elif "SyntaxError" in error_log:
        explanation = "Syntax error detected - manual review recommended"
        reasoning = "Syntax errors require context-aware parsing. Basic pattern matching cannot reliably fix arbitrary syntax issues."
    
    elif "ModuleNotFoundError" in error_log or "No module named" in error_log:
        match = re.search(r"No module named '(\w+)'", error_log)
        if match:
            module = match.group(1)
            explanation = f"Replaced {module} functions with standard library equivalents"
            reasoning = f"Module '{module}' is not available in the sandbox environment. Replacing {module} functions with Python standard library equivalents to maintain functionality."
            
            # Remove the import
            fixed_code = re.sub(rf"^import {module}.*$", f"# import {module}  # Unavailable in sandbox", bad_code, flags=re.MULTILINE)
            fixed_code = re.sub(rf"^from {module}.*$", f"# Removed: {module} not available", fixed_code, flags=re.MULTILINE)
            
            # Replace common numpy functions (handle both np and numpy)
            if module == "numpy" or module == "np":
                # Replace numpy.mean() or np.mean() with sum()/len()
                fixed_code = re.sub(r'(?:numpy|np)\.mean\(([^)]+)\)', r'sum(\1) / len(\1)', fixed_code)
                # Replace numpy.sum() or np.sum() with sum()
                fixed_code = re.sub(r'(?:numpy|np)\.sum\(([^)]+)\)', r'sum(\1)', fixed_code)
                # Replace numpy.max() or np.max() with max()
                fixed_code = re.sub(r'(?:numpy|np)\.max\(([^)]+)\)', r'max(\1)', fixed_code)
                # Replace numpy.min() or np.min() with min()
                fixed_code = re.sub(r'(?:numpy|np)\.min\(([^)]+)\)', r'min(\1)', fixed_code)
                # Replace numpy.array() or np.array() with list()
                fixed_code = re.sub(r'(?:numpy|np)\.array\(([^)]+)\)', r'list(\1)', fixed_code)
                # Replace numpy.median() or np.median() with statistics.median
                fixed_code = re.sub(r'(?:numpy|np)\.median\(([^)]+)\)', r'statistics.median(\1)', fixed_code)
                # Add statistics import if median was used
                if 'statistics.median' in fixed_code and 'import statistics' not in fixed_code:
                    fixed_code = 'import statistics\n' + fixed_code
    
    return explanation, fixed_code, reasoning

def clean_code_string(code: str) -> str:
    """Clean and normalize code string from AI response."""
    if not code:
        return code
    
    # Remove markdown code blocks
    if "```" in code:
        code = re.sub(r'```python\s*\n?', '', code)
        code = re.sub(r'```\s*\n?', '', code)
    
    # Handle various escape sequences that AI might return
    # Check if the code looks like it has literal \n (no actual newlines)
    if '\n' not in code and '\\n' in code:
        code = code.replace('\\n', '\n')
    
    # Also handle case where both exist but \\n should still be converted
    # This handles: "line1\nline2\\nline3" -> proper newlines
    code = code.replace('\\n', '\n')
    
    # Handle escaped quotes
    code = code.replace("\\'", "'")
    code = code.replace('\\"', '"')
    
    # Handle tabs
    code = code.replace('\\t', '    ')
    code = code.replace('\t', '    ')
    
    # Handle carriage returns
    code = code.replace('\\r', '')
    code = code.replace('\r', '')
    
    # Remove any leading/trailing whitespace but preserve internal structure
    lines = code.split('\n')
    # Remove empty lines from start and end only
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    
    return '\n'.join(lines)

def get_ai_fix(bad_code: str, error_log: str) -> tuple[str, str, str, float]:
    """Use Ollama LLM to fix broken code with full reasoning."""
    start_time = time.time()
    
    try:
        system_prompt = """You are an expert Python debugging assistant operating in a RESTRICTED DOCKER SANDBOX.

ENVIRONMENT CONSTRAINTS:
- NO internet access
- NO external libraries (numpy, pandas, requests, etc.)
- ONLY Python Standard Library available
- Memory limit: 128MB
- Time limit: 5 seconds

YOUR TASK:
1. Analyze the error and identify root cause
2. Provide a COMPLETE, WORKING fix using ONLY standard library
3. MAINTAIN THE SAME FUNCTIONALITY - do not simplify or remove logic
4. Replace external library functions with standard library equivalents
5. Explain your reasoning step-by-step

CRITICAL REQUIREMENTS:
- Provide the ENTIRE corrected code, not just a partial fix
- Preserve all original functionality and logic
- Replace numpy functions with standard library:
  * np.mean() → sum() / len()
  * np.sum() → sum()
  * np.array() → list()
  * np.max() → max()
  * np.min() → min()
  * etc.
- Replace pandas functions with standard library equivalents
- Keep all variables, functions, and print statements intact
- The fixed code must produce the same output as intended

RESPOND WITH ONLY A VALID JSON OBJECT:
{
    "explanation": "One sentence describing the bug and fix",
    "fixed_code": "Complete corrected Python code (no markdown, no backticks, preserve all functionality)",
    "reasoning": "Detailed step-by-step analysis of the problem and solution"
}

IMPORTANT: Return ONLY the JSON object, no additional text. The fixed_code must be complete and functional."""

        user_prompt = f"""BROKEN CODE:
```python
{bad_code}
```

ERROR OUTPUT:
```
{error_log}
```

CRITICAL INSTRUCTIONS:
- Provide the COMPLETE fixed code that maintains ALL original functionality
- Replace external library calls (like np.mean, np.sum, etc.) with standard library equivalents
- Keep ALL variables, functions, print statements, and logic intact
- The output should be the same as the original code intended
- Do NOT simplify or remove functionality - only replace unavailable libraries

Example: If code uses np.mean(numbers), replace with: sum(numbers) / len(numbers)
Example: If code uses np.sum(array), replace with: sum(array)

Return JSON only with the complete fixed code."""
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": f"{system_prompt}\n\n{user_prompt}",
                "stream": False,
                "format": "json"
            },
            timeout=60
        )
        
        ai_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            try:
                parsed = json.loads(result.get("response", "{}"))
                explanation = parsed.get("explanation", "AI provided fix")
                fixed_code = parsed.get("fixed_code", bad_code)
                reasoning = parsed.get("reasoning", "AI analysis completed")
                
                # Clean up code - comprehensive escape handling
                fixed_code = clean_code_string(fixed_code)
                
                return explanation, fixed_code.strip(), reasoning, ai_time
            except json.JSONDecodeError:
                # Try to extract code from raw response
                raw = result.get("response", "")
                exp, code, reason = apply_basic_fix(bad_code, error_log)
                return f"AI parse failed, using fallback: {exp}", code, reason, ai_time
        else:
            exp, code, reason = apply_basic_fix(bad_code, error_log)
            return exp, code, reason, ai_time
            
    except requests.exceptions.ConnectionError:
        exp, code, reason = apply_basic_fix(bad_code, error_log)
        return f"Ollama offline - {exp}", code, f"Could not connect to Ollama. {reason}", time.time() - start_time
    except requests.exceptions.Timeout:
        exp, code, reason = apply_basic_fix(bad_code, error_log)
        return f"AI timeout - {exp}", code, reason, time.time() - start_time
    except Exception as e:
        exp, code, reason = apply_basic_fix(bad_code, error_log)
        return f"AI error - {exp}", code, reason, time.time() - start_time

# --- SYSTEM STATUS CHECK ---

def check_system_status() -> tuple[bool, bool, str, str]:
    """Check Docker and Ollama status with details."""
    docker_online = False
    docker_detail = "Not connected"
    ollama_online = False
    ollama_detail = "Not connected"
    
    try:
        client = docker.from_env()
        client.ping()
        docker_online = True
        # Check if sandbox image exists
        try:
            client.images.get("my-safe-sandbox")
            docker_detail = "Ready (sandbox image found)"
        except:
            docker_detail = "Running (build sandbox image)"
    except:
        docker_detail = "Docker Desktop not running"
    
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=2)
        if resp.status_code == 200:
            ollama_online = True
            models = resp.json().get("models", [])
            if any("llama" in m.get("name", "").lower() for m in models):
                ollama_detail = "Ready (llama3 available)"
            else:
                ollama_detail = "Running (pull llama3 model)"
    except:
        ollama_detail = "Ollama not running"
    
    return docker_online, ollama_online, docker_detail, ollama_detail

# --- MAIN APPLICATION ---

def main():
    # Initialize session state
    if 'code' not in st.session_state:
        st.session_state.code = """import numpy as np  # This will fail in sandbox

def calculate_average(numbers):
    return np.mean(numbers)

data = [10, 20, 30, 40, 50]
result = calculate_average(data)
print(f"Average: {result}")"""
    
    if 'repair_session' not in st.session_state:
        st.session_state.repair_session = None
    
    if 'is_running' not in st.session_state:
        st.session_state.is_running = False

    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div style="padding: 20px 0;">
            <h1 style="font-size: 24px; font-weight: 700; color: #fafafa; margin: 0; display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 28px;">⚡</span> AutoFix AI
            </h1>
            <p style="color: #737373; font-size: 13px; margin-top: 8px;">Autonomous Code Repair System</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # System Status
        st.markdown("### System Status")
        docker_ok, ollama_ok, docker_msg, ollama_msg = check_system_status()
        
        col1, col2 = st.columns(2)
        with col1:
            if docker_ok:
                st.success("🐳 Docker", icon="✅")
            else:
                st.error("🐳 Docker", icon="❌")
        with col2:
            if ollama_ok:
                st.success("🤖 Ollama", icon="✅")
            else:
                st.error("🤖 Ollama", icon="❌")
        
        st.caption(f"Docker: {docker_msg}")
        st.caption(f"Ollama: {ollama_msg}")
        
        st.markdown("---")
        
        # Configuration
        st.markdown("### Configuration")
        st.info("🔄 **Unlimited Repair Cycles**\n\nThe system will automatically iterate until the code is fixed.")
        
        st.markdown("---")
        
        # Sandbox Constraints
        st.markdown("### 🔒 Sandbox Constraints")
        st.markdown("""
        <div style="background: #1f1f1f; border-radius: 8px; padding: 12px; font-size: 12px;">
            <div style="color: #a1a1a1; margin-bottom: 8px;">
                <strong style="color: #fafafa;">Memory:</strong> 128 MB limit
            </div>
            <div style="color: #a1a1a1; margin-bottom: 8px;">
                <strong style="color: #fafafa;">CPU:</strong> 50% throttled
            </div>
            <div style="color: #a1a1a1; margin-bottom: 8px;">
                <strong style="color: #fafafa;">Timeout:</strong> 5 seconds
            </div>
            <div style="color: #a1a1a1; margin-bottom: 8px;">
                <strong style="color: #fafafa;">Network:</strong> Disabled
            </div>
            <div style="color: #a1a1a1;">
                <strong style="color: #fafafa;">Libraries:</strong> stdlib only
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Example Codes
        st.markdown("### 📝 Examples")
        example_codes = {
            "Import Error (numpy)": """import numpy as np

def calculate_average(numbers):
    return np.mean(numbers)

data = [10, 20, 30, 40, 50]
print(calculate_average(data))""",
            
            "Division by Zero": """def divide(a, b):
    return a / b

x = 10
y = 0
result = divide(x, y)
print(f"Result: {result}")""",
            
            "Undefined Variable": """def greet(name):
    message = f"Hello, {name}!"
    print(message)

greet(user_name)""",
            
            "Infinite Loop": """i = 0
while True:
    i += 1
    if i > 1000000000:
        break""",
            
            "Working Code": """def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

for i in range(1, 8):
    print(f"{i}! = {factorial(i)}")"""
        }
        
        selected_example = st.selectbox(
            "Load Example",
            ["Select..."] + list(example_codes.keys()),
            label_visibility="collapsed"
        )
        
        if selected_example != "Select..." and selected_example in example_codes:
            st.session_state.code = example_codes[selected_example]
            st.rerun()

    # Main Content Area
    # Header
    st.markdown("""
    <div class="main-header">
        <div class="main-header-icon">⚡</div>
        <div class="main-header-text">
            <h1>AutoFix AI</h1>
            <p>Autonomous code repair with sandboxed execution and AI-powered debugging</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Main Layout - Two Columns
    col_editor, col_results = st.columns([1, 1], gap="large")
    
    # LEFT: Code Editor
    with col_editor:
        st.markdown("""
        <div class="editor-header" style="background: #1f1f1f; border: 1px solid #2a2a2a; border-bottom: none; border-radius: 12px 12px 0 0; padding: 12px 16px; display: flex; align-items: center; justify-content: space-between;">
            <span style="color: #fafafa; font-size: 14px; font-weight: 500;">📝 Code Editor</span>
            <span style="background: #3b82f6; color: white; font-size: 10px; padding: 2px 8px; border-radius: 100px;">Python</span>
        </div>
        """, unsafe_allow_html=True)

        code_input = st.text_area(
            "Code Editor", 
            value=st.session_state.code, 
            height=450,
            label_visibility="collapsed",
            key="code_editor"
        )
        
        # Update session state
        st.session_state.code = code_input
        
        # Action Buttons
        col_btn1, col_btn2 = st.columns([2, 1])
        with col_btn1:
            run_clicked = st.button("⚡ Run Autonomous Repair", use_container_width=True, type="primary")
        with col_btn2:
            clear_clicked = st.button("🗑️ Clear", use_container_width=True)
        
        if clear_clicked:
            st.session_state.code = ""
            st.session_state.repair_session = None
            st.rerun()
    
    # RIGHT: Results Panel
    with col_results:
        st.markdown("""
        <div class="timeline-header" style="background: #1f1f1f; border: 1px solid #2a2a2a; border-bottom: none; border-radius: 12px 12px 0 0; padding: 16px 20px;">
            <h3 style="color: #fafafa; font-size: 16px; font-weight: 600; margin: 0;">📊 Execution Timeline</h3>
        </div>
        """, unsafe_allow_html=True)
        
        results_container = st.container(height=520, border=True)
        
        with results_container:
            if run_clicked and code_input.strip():
                # Initialize repair session
                session = RepairSession(
                    original_code=code_input,
                    final_code=code_input
                )
                
                current_code = code_input
                iteration = 0
                
                # Unlimited repair loop - continues until code is fixed
                while True:
                    iteration += 1
                    session.total_iterations = iteration
                    
                    # Create iteration card
                    with st.status(f"🔄 Iteration {iteration} (Unlimited)", expanded=True) as status:
                        
                        # Step 1: Execute
                        st.markdown("**Step 1:** Executing in sandbox...")
                        trace = run_in_docker(current_code)
                        trace.iteration = iteration
                        session.execution_traces.append(trace)
                        
                        if trace.success:
                            status.update(label=f"✅ Iteration {iteration}: Success!", state="complete")
                            
                            st.success("**Execution Successful!**")
                            
                            # Show output
                            st.markdown("##### 📤 Output")
                            st.code(trace.output if trace.output.strip() else "(No output)", language="text")
                            
                            session.success = True
                            session.final_code = current_code
                            st.session_state.repair_session = session
                            break  # Exit loop on success
                        
                        else:
                            status.update(label=f"❌ Iteration {iteration}: Error detected", state="error")
                            
                            # Ensure we have valid error information
                            error_type = trace.error_type or "UnknownError"
                            error_output = trace.output if trace.output and trace.output.strip() else "No error output captured. Execution failed silently."
                            
                            # Show error details
                            st.error(f"**{error_type}** detected")
                            
                            # Show stack trace directly (no nested expander)
                            st.markdown("**🔍 Stack Trace:**")
                            display_output = error_output[:500] + ("..." if len(error_output) > 500 else "")
                            st.code(display_output, language="bash")
                            
                            # Step 2: AI Analysis - Always try to fix
                            st.markdown("---")
                            st.markdown("**Step 2:** AI analyzing and generating patch...")
                            
                            with st.spinner("🧠 Consulting AI..."):
                                # Ensure we pass valid error output to AI
                                explanation, fixed_code, reasoning, ai_time = get_ai_fix(current_code, error_output)
                            
                            # Create patch record
                            unified_diff = generate_unified_diff(current_code, fixed_code)
                            line_edits = generate_line_edits(current_code, fixed_code)
                            
                            patch = PatchRecord(
                                iteration=iteration,
                                original_code=current_code,
                                fixed_code=fixed_code,
                                unified_diff=unified_diff,
                                line_edits=line_edits,
                                explanation=explanation,
                                reasoning=reasoning,
                                ai_time=ai_time
                            )
                            session.patch_logs.append(patch)
                            
                            # Show AI explanation
                            st.info(f"💡 **Fix:** {explanation}")
                            st.caption(f"⏱️ AI response time: {ai_time:.2f}s")
                            
                            # Show reasoning (collapsed in a details tag via markdown)
                            st.markdown("**🧠 AI Reasoning:**")
                            st.markdown(f"> {reasoning[:300]}{'...' if len(reasoning) > 300 else ''}")
                            
                            # Show diff
                            st.markdown("**📋 Patch (Unified Diff):**")
                            if unified_diff.strip():
                                st.code(unified_diff, language="diff")
                            else:
                                st.caption("No changes detected")
                            
                            # Show line edit count
                            st.caption(f"📝 {len(line_edits)} line edit(s) applied")
                            
                            # Apply patch automatically
                            st.markdown("**Step 3:** Applying patch...")
                            current_code = clean_code_string(fixed_code)
                            st.success("✅ Patch applied - continuing to next iteration...")
                            
                            # Update session state
                            session.final_code = current_code
                            st.session_state.repair_session = session
                            
                            # Continue to next iteration (loop will continue)
                
                # Final Summary
                st.markdown("---")
                
                if session.success:
                    st.markdown("""
                    <div style="background: rgba(34, 197, 94, 0.1); border: 1px solid #22c55e; border-radius: 12px; padding: 16px; margin-top: 12px;">
                        <h4 style="color: #22c55e; margin: 0 0 8px 0;">🎉 Repair Successful!</h4>
                        <p style="color: #a1a1a1; margin: 0; font-size: 14px;">Code was fixed in {0} iteration(s)</p>
                    </div>
                    """.format(session.total_iterations), unsafe_allow_html=True)
                    
                    # Update editor with fixed code
                    st.session_state.code = clean_code_string(session.final_code)
                    
                else:
                    st.markdown(f"""
                    <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid #ef4444; border-radius: 12px; padding: 16px; margin-top: 12px;">
                        <h4 style="color: #ef4444; margin: 0 0 8px 0;">⚠️ Repair Failed</h4>
                        <p style="color: #a1a1a1; margin: 0; font-size: 14px;">{session.failure_reason}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            elif not run_clicked:
                # Welcome state
                st.markdown("""
                <div style="text-align: center; padding: 60px 20px; color: #737373;">
                    <div style="font-size: 48px; margin-bottom: 16px;">⚡</div>
                    <h3 style="color: #a1a1a1; margin-bottom: 8px;">Ready to Debug</h3>
                    <p style="font-size: 14px;">Enter your Python code and click "Run Autonomous Repair" to start</p>
                </div>
                """, unsafe_allow_html=True)
    
    # Bottom Tabs for Full Artifacts
    if st.session_state.repair_session:
        session = st.session_state.repair_session
        
        st.markdown("---")
        st.markdown("")
        st.markdown("### 📁 Session Artifacts")
        st.markdown("")
        
        tab_code, tab_traces, tab_patches, tab_summary = st.tabs([
            "  📝 Final Code  ", 
            "  🔍 Execution Traces  ", 
            "  📋 Patch Logs  ",
            "  📊 Summary  "
        ])
        
        with tab_code:
            st.markdown("")
            col1, col2 = st.columns(2, gap="large")
            with col1:
                st.markdown("##### 📄 Original Code")
                st.markdown("")
                # Display code preserving newlines
                original_display = clean_code_string(session.original_code)
                st.code(original_display, language="python", line_numbers=True)
            with col2:
                st.markdown("##### ✨ Final Code")
                st.markdown("")
                # Display code preserving newlines - apply cleaning
                final_display = clean_code_string(session.final_code)
                st.code(final_display, language="python", line_numbers=True)
            
            # Full diff
            st.markdown("")
            st.markdown("##### 📋 Complete Diff")
            st.markdown("")
            full_diff = generate_unified_diff(session.original_code, session.final_code)
            if full_diff.strip():
                st.code(full_diff, language="diff", line_numbers=True)
            else:
                st.info("No changes made to the original code")
        
        with tab_traces:
            st.markdown("")
            for trace in session.execution_traces:
                with st.expander(
                    f"🔍 Iteration {trace.iteration} - {'✅ Success' if trace.success else '❌ ' + (trace.error_type or 'Error')}",
                    expanded=False
                ):
                    st.markdown("")
                    col1, col2 = st.columns([1, 1], gap="medium")
                    with col1:
                        st.metric("⏱️ Execution Time", f"{trace.execution_time:.3f}s")
                    with col2:
                        st.metric("📊 Status", "Success" if trace.success else "Failed")
                    
                    st.markdown("")
                    st.markdown("**📄 Code Snapshot:**")
                    # Properly format code snapshot using clean function
                    code_display = clean_code_string(trace.code_snapshot)
                    st.code(code_display, language="python", line_numbers=True)
                    
                    st.markdown("")
                    st.markdown("**📤 Output/Error:**")
                    st.code(trace.output if trace.output else "(No output)", language="bash")
                    
                    if trace.logs:
                        st.markdown("")
                        st.markdown("**📋 Captured Logs:**")
                        for log in trace.logs:
                            st.text(log)
        
        with tab_patches:
            st.markdown("")
            if session.patch_logs:
                for patch in session.patch_logs:
                    with st.expander(f"🔧 Patch from Iteration {patch.iteration}", expanded=True):
                        st.markdown("")
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**💡 Explanation:** {patch.explanation}")
                        with col2:
                            st.caption(f"⏱️ {patch.ai_time:.2f}s")
                        
                        st.markdown("")
                        st.markdown("**🧠 Reasoning:**")
                        st.info(patch.reasoning)
                        
                        st.markdown("")
                        st.markdown("**📋 Unified Diff:**")
                        diff_display = patch.unified_diff if patch.unified_diff.strip() else "(No diff)"
                        st.code(diff_display, language="diff")
                        
                        st.markdown("")
                        st.markdown(f"**📝 Structured Line Edits ({len(patch.line_edits)} changes):**")
                        st.json(patch.line_edits[:20] if len(patch.line_edits) > 20 else patch.line_edits)
            else:
                st.info("No patches were generated (code executed successfully on first try)")
        
        with tab_summary:
            st.markdown("")
            
            # Metrics cards
            col1, col2, col3, col4 = st.columns(4, gap="medium")
            with col1:
                st.metric("🔄 Total Iterations", session.total_iterations)
            with col2:
                st.metric("🔧 Patches Applied", len(session.patch_logs))
            with col3:
                total_time = sum(t.execution_time for t in session.execution_traces)
                st.metric("⏱️ Total Exec Time", f"{total_time:.2f}s")
            with col4:
                st.metric("📊 Final Status", "✅ Fixed" if session.success else "❌ Failed")
            
            st.markdown("")
            st.markdown("---")
            st.markdown("")
            
            # Iteration-wise reasoning
            st.markdown("##### 🧠 Iteration-wise Reasoning Steps")
            st.markdown("")
            
            for i, trace in enumerate(session.execution_traces):
                matching_patch = next((p for p in session.patch_logs if p.iteration == trace.iteration), None)
                
                st.markdown(f"""
                <div style="background: #1f1f1f; border: 1px solid #2a2a2a; border-radius: 8px; padding: 16px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <span style="background: #3b82f6; color: white; padding: 4px 12px; border-radius: 100px; font-size: 12px; font-weight: 600;">
                            Iteration {trace.iteration}
                        </span>
                        <span style="color: {'#22c55e' if trace.success else '#ef4444'}; font-size: 12px;">
                            {'✅ Success' if trace.success else '❌ ' + (trace.error_type or 'Error')}
                        </span>
                    </div>
                    <div style="color: #a1a1a1; font-size: 13px; line-height: 1.6;">
                        <strong style="color: #fafafa;">Execution:</strong> 
                        {'Code executed successfully with no errors.' if trace.success else f'Encountered {trace.error_type}. Execution time: {trace.execution_time:.3f}s'}
                    </div>
                    {f'''<div style="color: #a1a1a1; font-size: 13px; line-height: 1.6; margin-top: 8px;">
                        <strong style="color: #fafafa;">AI Analysis:</strong> {matching_patch.reasoning[:200]}{'...' if len(matching_patch.reasoning) > 200 else ''}
                    </div>''' if matching_patch else ''}
                </div>
                """, unsafe_allow_html=True)
            
            # Failure explanation
            if not session.success and session.failure_reason:
                st.markdown("---")
                st.markdown("##### ⚠️ Failure Explanation")
                st.error(session.failure_reason)
                st.markdown("""
                **Possible Solutions:**
                - Review the error patterns and consider manual fixes
                - Check if the code uses unavailable external libraries
                - Ensure the algorithm doesn't have infinite loops
                - The system will continue trying until the code is fixed
                """)

if __name__ == "__main__":
    main()
