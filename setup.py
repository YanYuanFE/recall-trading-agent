#!/usr/bin/env python3
"""
Setup script for Recall Trading Agent
"""

import os
import subprocess
import sys

def create_virtual_environment():
    """Create virtual environment if it doesn't exist"""
    if not os.path.exists('.venv'):
        print("Creating virtual environment...")
        subprocess.run([sys.executable, '-m', 'venv', '.venv'])
        print("Virtual environment created successfully!")
    else:
        print("Virtual environment already exists.")

def install_requirements():
    """Install requirements using pip"""
    print("Installing requirements...")
    
    # Determine the correct pip path
    if os.name == 'nt':  # Windows
        pip_path = '.venv/Scripts/pip'
    else:  # Unix/Linux/macOS
        pip_path = '.venv/bin/pip'
    
    subprocess.run([pip_path, 'install', '-r', 'requirements.txt'])
    print("Requirements installed successfully!")

def setup_environment():
    """Set up environment file"""
    if not os.path.exists('.env'):
        print("Creating .env file from template...")
        with open('.env.example', 'r') as template:
            content = template.read()
        
        with open('.env', 'w') as env_file:
            env_file.write(content)
        
        print("Environment file created! Please edit .env with your API credentials.")
    else:
        print("Environment file already exists.")

def create_directories():
    """Create necessary directories"""
    directories = ['logs', 'tests']
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")

def main():
    """Main setup function"""
    print("Setting up Recall Trading Agent...")
    print("=" * 50)
    
    try:
        create_virtual_environment()
        install_requirements()
        setup_environment()
        create_directories()
        
        print("=" * 50)
        print("Setup completed successfully!")
        print()
        print("Next steps:")
        print("1. Edit .env file with your Recall API credentials")
        print("2. Activate virtual environment:")
        if os.name == 'nt':
            print("   .venv\\Scripts\\activate")
        else:
            print("   source .venv/bin/activate")
        print("3. Run the agent:")
        print("   python main.py")
        
    except Exception as e:
        print(f"Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()