"""
Debug Setup Script - Check if all components are ready
Run this before using the Self-Healing Code Dashboard
"""

import sys
import subprocess


def check_component(name, check_func):
    """Helper to check a component and print status"""
    print(f"\n{'='*60}")
    print(f"Checking: {name}")
    print('='*60)
    try:
        result = check_func()
        if result:
            print(f"✅ {name}: OK")
            return True
        else:
            print(f"❌ {name}: FAILED")
            return False
    except Exception as e:
        print(f"❌ {name}: ERROR - {str(e)}")
        return False


def check_python_packages():
    """Check if required Python packages are installed"""
    required = ['streamlit', 'docker', 'requests']
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"  ✓ {package} installed")
        except ImportError:
            print(f"  ✗ {package} NOT installed")
            missing.append(package)
    
    if missing:
        print(f"\n  Install missing packages:")
        print(f"  pip install {' '.join(missing)}")
        return False
    return True


def check_docker():
    """Check if Docker is running and accessible"""
    try:
        import docker
        client = docker.from_env()
        
        # Try to ping Docker
        client.ping()
        print("  ✓ Docker is running")
        
        # Check for the sandbox image
        try:
            client.images.get('my-safe-sandbox')
            print("  ✓ 'my-safe-sandbox' image found")
        except docker.errors.ImageNotFound:
            print("  ✗ 'my-safe-sandbox' image NOT found")
            print("\n  Create the image:")
            print("  1. Create a Dockerfile with:")
            print("     FROM python:3.11-slim")
            print("     WORKDIR /app")
            print("  2. Run: docker build -t my-safe-sandbox .")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ✗ Docker error: {str(e)}")
        print("\n  Make sure Docker Desktop is running")
        return False


def check_ollama():
    """Check if Ollama is running and has llama3 model"""
    try:
        import requests
        
        # Check if Ollama is running
        try:
            response = requests.get('http://localhost:11434/api/tags', timeout=2)
            if response.status_code == 200:
                print("  ✓ Ollama is running")
                
                # Check for llama3 model
                models = response.json().get('models', [])
                model_names = [m.get('name', '') for m in models]
                
                if any('llama3' in name for name in model_names):
                    print("  ✓ llama3 model found")
                    return True
                else:
                    print("  ✗ llama3 model NOT found")
                    print("\n  Install llama3:")
                    print("  ollama pull llama3")
                    return False
            else:
                print("  ✗ Ollama not responding correctly")
                return False
                
        except requests.exceptions.ConnectionError:
            print("  ✗ Cannot connect to Ollama")
            print("\n  Start Ollama:")
            print("  ollama serve")
            return False
            
    except ImportError:
        print("  ✗ requests package not installed")
        return False


def check_streamlit_running():
    """Check if Streamlit is currently running"""
    try:
        import requests
        response = requests.get('http://localhost:8501', timeout=2)
        print("  ✓ Streamlit is running on http://localhost:8501")
        return True
    except:
        print("  ✗ Streamlit is NOT running")
        print("\n  Start Streamlit:")
        print("  streamlit run app.py")
        return False


def main():
    print("\n" + "="*60)
    print("Self-Healing Code Dashboard - Setup Check")
    print("="*60)
    
    results = {
        'Python Packages': check_component('Python Packages', check_python_packages),
        'Docker': check_component('Docker & Sandbox Image', check_docker),
        'Ollama': check_component('Ollama & llama3', check_ollama),
        'Streamlit': check_component('Streamlit Server', check_streamlit_running),
    }
    
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    
    for component, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {component}")
    
    all_ready = all(results.values())
    
    print("\n" + "="*60)
    if all_ready:
        print("🎉 All systems ready! Go to http://localhost:8501")
    else:
        print("⚠️  Some components need attention")
        print("\nQuick Start Guide:")
        print("1. Install packages: pip install streamlit docker requests")
        print("2. Start Docker Desktop")
        print("3. Build image: docker build -t my-safe-sandbox .")
        print("4. Start Ollama: ollama serve")
        print("5. Pull model: ollama pull llama3")
        print("6. Run app: streamlit run app.py")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
