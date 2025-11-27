# ⚡ AutoFix AI - Autonomous Code Repair System

An intelligent Python debugging system that automatically detects, analyzes, and fixes code errors using AI-powered analysis and secure Docker sandbox execution. Built with Streamlit, Docker, and Ollama (Llama3).

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.39.0-red.svg)
![Docker](https://img.shields.io/badge/Docker-Required-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 🌟 Features

### 🔒 Secure Sandbox Execution

Runs Python code in isolated Docker containers with strict security constraints:

- **Memory Limit**: 128MB
- **CPU**: 50% throttled (50,000/100,000)
- **Network**: Completely disabled
- **Timeout**: 5-second hard limit
- **Libraries**: Python standard library only

### 🤖 AI-Powered Auto-Repair

Uses local Ollama (Llama3) to intelligently fix code:

- **Error Analysis**: Extracts error types and stack traces
- **Root Cause Detection**: Identifies the underlying problem
- **Structured Fixes**: Generates JSON-formatted patches with:
  - Complete fixed code
  - Detailed explanation
  - Step-by-step reasoning
  - Unified diffs
  - Line-by-line edit instructions

### 🎨 Modern Ollama-Style UI

Professional dark-themed dashboard featuring:

- **Real-time System Status**: Docker and Ollama connectivity monitoring
- **Live Execution Timeline**: Interactive iteration tracking with expandable details
- **Code Editor**: Syntax-highlighted Python editor
- **Visual Diff Viewer**: Color-coded code changes
- **Comprehensive Artifacts**: Full session logs, patches, and traces
- **Built-in Examples**: Pre-loaded error scenarios for testing

### 📊 Complete Session Tracking

Captures all debugging details:

- **Execution Traces**: Code snapshots, outputs, errors, timing
- **Patch Records**: Original/fixed code, diffs, AI reasoning
- **Repair Sessions**: Complete audit trail of all repair attempts

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+**
2. **Docker Desktop** (running)
3. **Ollama** with Llama3 model

### Installation

1. **Clone the repository**

```bash
git clone <your-repo-url>
cd PythonProject
```

2. **Install Python dependencies**

```bash
pip install -r requirements.txt
```

3. **Build the Docker sandbox image**

```bash
docker build -t my-safe-sandbox .
```

4. **Install and start Ollama**

```bash
# Install Ollama (visit https://ollama.ai)
ollama pull llama3
ollama serve
```

### Running the Application

```bash
streamlit run app.py
```

The dashboard will open at `http://localhost:8501`

## 📋 Usage

### Basic Workflow

1. **Enter/Load Code**:

   - Type Python code directly in the editor
   - Or select from pre-loaded examples (Import Error, Division by Zero, Undefined Variable, Infinite Loop, Working Code)

2. **Configure Settings**:

   - Adjust "Max Repair Cycles" (1-10 iterations)
   - System status indicators show Docker and Ollama readiness

3. **Start Repair**:

   - Click "⚡ Run Autonomous Repair"
   - Watch real-time execution in the timeline panel

4. **Review Results**:
   - Each iteration shows:
     - Execution status (Success/Error)
     - Stack traces and error details
     - AI reasoning and explanation
     - Applied patches with unified diffs
   - View comprehensive artifacts in bottom tabs

### Example Error Scenarios

The app includes 5 built-in examples:

- **Import Error**: Code using unavailable libraries (numpy)
- **Division by Zero**: Unhandled division errors
- **Undefined Variable**: Missing variable definitions
- **Infinite Loop**: Code exceeding timeout limits
- **Working Code**: Valid code that executes successfully

### Fallback Fix Strategies

When Ollama is unavailable, the system uses intelligent pattern-based fixes:

- **ZeroDivisionError**: Wraps divisions in try-except blocks
- **NameError**: Auto-defines missing variables with None
- **IndentationError**: Normalizes to 4-space indentation
- **ModuleNotFoundError**: Comments out unavailable imports with explanatory notes
- **SyntaxError**: Provides detailed recommendations for manual review

## 📁 Project Structure

```
PythonProject/
├── app.py                 # Main Streamlit application (850+ lines)
│   ├── Data Structures    # ExecutionTrace, PatchRecord, RepairSession
│   ├── UI Components      # Modern dark theme CSS (Ollama-style)
│   ├── Docker Integration # Sandbox execution with security limits
│   ├── AI Integration     # Ollama/Llama3 fix generation
│   └── Utilities          # Diff generation, error parsing, code cleaning
├── Dockerfile            # Docker sandbox configuration
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## 🎨 UI Components

### Main Dashboard

- **Header**: System branding with gradient effects
- **Code Editor**: Full-featured Python code input with syntax highlighting
- **Timeline Panel**: Real-time execution logs with expandable iterations
- **Status Pills**: Live Docker and Ollama connection indicators

### Session Artifacts (Tabs)

1. **📝 Final Code**: Side-by-side comparison of original vs fixed code with complete diff
2. **🔍 Execution Traces**: Detailed logs of each execution attempt with code snapshots
3. **📋 Patch Logs**: All AI-generated fixes with reasoning and structured edits
4. **📊 Summary**: Metrics dashboard and iteration-wise reasoning steps

## 🔧 Configuration

### Docker Sandbox Settings

Modify in `run_in_docker()` function:

```python
mem_limit="128m",          # Memory limit
cpu_period=100000,         # CPU period
cpu_quota=50000,           # CPU quota (50% throttle)
network_disabled=True,     # Disable network access
timeout=5                  # Execution timeout in seconds
```

### AI Model Configuration

Change the model in `get_ai_fix()` function:

```python
"model": "llama3",  # Options: llama3, codellama, mistral, etc.
```

### Max Iterations

Adjustable via sidebar slider (default: 5, range: 1-10)

## 🧪 Testing

The application includes built-in test examples accessible from the sidebar:

- **Import Error (numpy)**: Tests handling of unavailable external libraries
- **Division by Zero**: Tests error handling for mathematical errors
- **Undefined Variable**: Tests name resolution fixes
- **Infinite Loop**: Tests timeout protection
- **Working Code**: Tests successful execution flow

### System Status Checks

The application automatically checks system status in the sidebar:

- ✅ Docker daemon running and sandbox image availability
- ✅ Ollama service accessibility and llama3 model presence
- Real-time connection monitoring with detailed status messages

## 🏗️ Technical Architecture

### Data Structures

**ExecutionTrace**

```python
@dataclass
class ExecutionTrace:
    iteration: int
    timestamp: str
    code_snapshot: str
    success: bool
    output: str
    error_type: Optional[str]
    stack_trace: Optional[str]
    logs: List[str]
    execution_time: float
```

**PatchRecord**

```python
@dataclass
class PatchRecord:
    iteration: int
    original_code: str
    fixed_code: str
    unified_diff: str
    line_edits: List[Dict[str, Any]]
    explanation: str
    reasoning: str
    ai_time: float
```

**RepairSession**

```python
@dataclass
class RepairSession:
    original_code: str
    final_code: str
    execution_traces: List[ExecutionTrace]
    patch_logs: List[PatchRecord]
    total_iterations: int
    success: bool
    failure_reason: Optional[str]
```

### Key Functions

- `run_in_docker()`: Executes code in isolated Docker container
- `get_ai_fix()`: Queries Ollama for fix generation with JSON response
- `apply_basic_fix()`: Fallback pattern-based fixes when AI unavailable
- `clean_code_string()`: Normalizes AI-generated code (handles escaped newlines, quotes)
- `generate_unified_diff()`: Creates standard unified diff format
- `generate_line_edits()`: Structured line-by-line edit instructions
- `check_system_status()`: Real-time Docker and Ollama connectivity check

### AI Prompt Strategy

The system uses a structured prompt for Ollama:

- **System Context**: Explains sandbox constraints (no network, stdlib only, 128MB RAM, 5s timeout)
- **User Input**: Provides broken code and error output
- **Response Format**: Enforces JSON structure with explanation, fixed_code, and reasoning fields
- **Code Cleaning**: Robust post-processing to handle escaped characters and markdown artifacts

## 🐛 Troubleshooting

### Docker Issues

**"Docker Desktop is not running"**

- Start Docker Desktop application
- Wait for Docker daemon to fully initialize
- Verify: `docker ps`

**"Image not found: my-safe-sandbox"**

```bash
docker build -t my-safe-sandbox .
```

**Container timeout/hanging**

- Check container logs: `docker logs <container_id>`
- Verify no infinite loops in code
- Ensure Docker has sufficient resources allocated

### Ollama Issues

**"Ollama not running"**

```bash
ollama serve
```

**"Model not found"**

```bash
ollama pull llama3
```

**Slow AI responses**

- First run downloads model (can take time)
- Subsequent runs should be faster
- Check system resources (CPU/RAM usage)

**Connection refused**

- Verify Ollama is running: `curl http://localhost:11434/api/tags`
- Check port 11434 is not blocked
- Restart Ollama service

### Streamlit Issues

**"Address already in use"**

```bash
streamlit run app.py --server.port 8502
```

**"ModuleNotFoundError"**

```bash
pip install -r requirements.txt
```

**UI not updating**

- Clear Streamlit cache: `streamlit cache clear`
- Hard refresh browser: `Ctrl+F5` / `Cmd+Shift+R`

**Code display issues (escaped newlines)**

- This is fixed in the code via `clean_code_string()` function
- Handles `\\n`, `\\'`, `\\"`, markdown code blocks

### Common Code Execution Errors

**"TimeoutError: Execution exceeded 5 seconds"**

- Check for infinite loops
- Reduce computational complexity
- Increase timeout in `run_in_docker()` (line ~370)

**"ModuleNotFoundError: No module named 'xyz'"**

- Sandbox only supports Python standard library
- Remove or replace external dependencies (numpy, pandas, requests, etc.)
- AI will attempt to rewrite using stdlib

**"MemoryError"**

- Code exceeds 128MB memory limit
- Reduce data structure sizes
- Optimize memory usage

## 🚀 Advanced Usage

### Custom Docker Image

Modify `Dockerfile` to add additional stdlib modules or tools:

```dockerfile
FROM python:3.9-slim
WORKDIR /app
# Add custom configurations here
CMD ["python"]
```

Rebuild:

```bash
docker build -t my-safe-sandbox .
```

### Different AI Models

Supported Ollama models:

- `llama3` (default, recommended)
- `codellama` (code-specialized)
- `mistral` (faster, smaller)
- `deepseek-coder` (code-focused)

Change in `app.py` line ~415:

```python
"model": "codellama",
```

### Extending Repair Logic

Add custom error patterns in `apply_basic_fix()` function (line ~385):

```python
elif "CustomError" in error_log:
    explanation = "Your fix description"
    reasoning = "Why this fix works"
    fixed_code = # Your fix logic
```

## 🎯 Use Cases

- **Education**: Teaching debugging and error handling
- **Rapid Prototyping**: Quick code validation without manual debugging
- **Code Review**: Automated first-pass error detection
- **Learning AI**: Understanding how LLMs approach code repair
- **Sandbox Testing**: Safe execution of untrusted code

## 🔐 Security Features

- **Network Isolation**: No external connections possible
- **Resource Limits**: Prevents resource exhaustion attacks
- **Timeout Protection**: Kills long-running processes
- **Filesystem Isolation**: Container-based separation
- **No Persistent State**: Each run is completely isolated

## 📊 Performance Metrics

Typical execution times:

- **Code Execution**: 0.1-5.0 seconds (depending on complexity)
- **AI Fix Generation**: 2-10 seconds (first run slower due to model loading)
- **Diff Generation**: <0.1 seconds
- **UI Rendering**: <0.5 seconds

## 🎨 Customization

### Theme Colors

Edit CSS variables in `app.py` (lines ~65-85):

```css
:root {
  --bg-primary: #0d0d0d;
  --accent-primary: #22c55e;
  /* Modify colors here */
}
```

### Sidebar Content

Modify sidebar section in `main()` function (line ~690):

```python
with st.sidebar:
    # Add custom widgets
    st.markdown("### Your Section")
```

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- Additional error pattern recognition
- Support for more programming languages
- Enhanced AI prompting strategies
- UI/UX improvements
- Performance optimizations

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **[Streamlit](https://streamlit.io/)**: Beautiful web UI framework
- **[Ollama](https://ollama.ai/)**: Local LLM inference
- **[Llama3](https://llama.meta.com/)**: Meta's powerful language model
- **[Docker](https://www.docker.com/)**: Containerization platform

## 📈 Future Enhancements

- [ ] Multi-language support (JavaScript, Java, C++)
- [ ] Historical session persistence
- [ ] Advanced metrics and analytics
- [ ] Collaborative debugging features
- [ ] Integration with VS Code extension
- [ ] Export repair logs as markdown reports
- [ ] Support for custom AI models via API
- [ ] Interactive code diff editor
- [ ] Real-time collaboration mode

## 📞 Support

For issues and questions:

- Open an issue on GitHub
- Check existing documentation
- Review troubleshooting section

---

**⚡ Built for autonomous code repair | Made with ❤️ using Streamlit, Docker, and AI**
