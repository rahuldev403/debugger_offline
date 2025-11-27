# 🔧 Local Autonomous Debugging System

A hackathon project that runs Python code in a secure Docker sandbox and uses AI (Ollama/Llama3) to automatically detect and fix bugs.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.39.0-red.svg)
![Docker](https://img.shields.io/badge/Docker-Required-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 🌟 Features

- **🔒 Secure Sandbox Execution**: Runs Python code in isolated Docker containers with:
  - 128MB memory limit
  - Network disabled
  - 5-second timeout protection
  
- **🤖 AI-Powered Auto-Repair**: Uses local Ollama (Llama3) to:
  - Analyze error messages
  - Generate structured fixes with explanations
  - Provide unified diffs of changes

- **📊 Professional Dashboard**: 
  - Real-time system status monitoring
  - Visual error traces and debugging workflow
  - Step-by-step repair process visualization

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

1. **Paste your Python code** in the code editor
2. **Click "▶ Start Debugging"** to run the code
3. **Watch the AI automatically fix errors** through multiple repair attempts
4. **View the unified diff** to see exactly what changed

## 🧪 Test Examples

Run the test examples to see the system in action:

```bash
python test_examples.py
```

This provides 10 different test cases including:
- Division by zero
- Type errors
- Import errors
- Syntax errors
- Timeout scenarios
- And more!

## 🛠️ System Check

Run the debug setup script to verify all components:

```bash
python debug_setup.py
```

This checks:
- ✅ Python packages installed
- ✅ Docker running & sandbox image exists
- ✅ Ollama running & llama3 model available
- ✅ Streamlit server status

## 📁 Project Structure

```
PythonProject/
├── app.py                 # Main Streamlit application
├── debug_setup.py         # System diagnostics tool
├── test_examples.py       # Test cases for the dashboard
├── Dockerfile            # Docker sandbox configuration
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## 🔧 Configuration

### Docker Sandbox Settings

The sandbox is configured with the following security constraints:

- **Memory Limit**: 128MB
- **Network**: Disabled
- **Timeout**: 5 seconds
- **Isolation**: Full container isolation

### AI Model

Default model: `llama3` (via Ollama)

To change the model, edit the `get_ai_fix()` function in `app.py`:

```python
"model": "llama3",  # Change to your preferred model
```

## 🎯 Hackathon Scoring Criteria

This project is designed to maximize points across:

1. **Sandbox Reliability** (✅ 128MB limit, ✅ Network disabled, ✅ Timeout protection)
2. **Structured Patching** (✅ JSON responses, ✅ Unified diffs, ✅ AI reasoning)
3. **User Experience** (✅ Professional UI, ✅ Real-time status, ✅ Clear visualization)

## 🐛 Troubleshooting

### Docker Issues
- Ensure Docker Desktop is running
- Verify the sandbox image exists: `docker images | grep my-safe-sandbox`
- Rebuild if needed: `docker build -t my-safe-sandbox .`

### Ollama Issues
- Check if Ollama is running: `curl http://localhost:11434/api/tags`
- Restart Ollama: `ollama serve`
- Pull model again: `ollama pull llama3`

### Streamlit Issues
- Clear cache: `streamlit cache clear`
- Check port availability: `netstat -an | grep 8501`

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Powered by [Ollama](https://ollama.ai/) and Llama3
- Containerized with [Docker](https://www.docker.com/)

## 📞 Support

For issues and questions, please open an issue on GitHub.

---

**Made with ❤️ for hackathons**
