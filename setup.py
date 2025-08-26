#!/usr/bin/env python3
"""
Setup script for Hope Foundation NGO Website
"""
import os
import subprocess
import sys

def run_command(command, description):
    """Run a system command and handle errors"""
    print(f"📦 {description}...")
    try:
        subprocess.check_call(command, shell=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        return False
    print(f"✅ Python {sys.version} is compatible")
    return True

def create_env_file():
    """Create .env file from example if it doesn't exist"""
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            with open('.env.example', 'r') as example:
                with open('.env', 'w') as env_file:
                    env_file.write(example.read())
            print("✅ Created .env file from .env.example")
            print("⚠️  Please edit .env file with your configuration")
        else:
            print("❌ .env.example file not found")
            return False
    else:
        print("✅ .env file already exists")
    return True

def main():
    """Main setup function"""
    print("🚀 Setting up Hope Foundation NGO Website Backend")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Create virtual environment
    if not os.path.exists('venv'):
        if not run_command('python -m venv venv', 'Creating virtual environment'):
            return False
    else:
        print("✅ Virtual environment already exists")
    
    # Activate virtual environment and install requirements
    if os.name == 'nt':  # Windows
        activate_cmd = 'venv\\Scripts\\activate.bat && '
        python_cmd = 'venv\\Scripts\\python'
    else:  # Unix/Linux/Mac
        activate_cmd = '. venv/bin/activate && '
        python_cmd = 'venv/bin/python'
    
    if not run_command(f'{python_cmd} -m pip install -r requirements.txt', 
                      'Installing Python dependencies'):
        return False
    
    # Create environment file
    if not create_env_file():
        return False
    
    # Initialize database
    if not run_command(f'{python_cmd} -c "from app import app, db; app.app_context().push(); db.create_all(); print(\'Database initialized successfully\')"', 
                      'Initializing database'):
        return False
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your email configuration (optional)")
    print("2. Run the application:")
    if os.name == 'nt':
        print("   venv\\Scripts\\activate.bat")
        print("   python app.py")
    else:
        print("   . venv/bin/activate")
        print("   python app.py")
    print("3. Open http://localhost:5000 in your browser")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)