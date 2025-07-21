#!/usr/bin/env python3
"""
HealthTwin AI Setup Script
Automated setup for development and production environments
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, cwd=None, check=True):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd, 
            check=check,
            capture_output=True,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error: {e.stderr}")
        if check:
            sys.exit(1)
        return e

def check_prerequisites():
    """Check if required tools are installed"""
    print("🔍 Checking prerequisites...")
    
    requirements = {
        'python': 'python --version',
        'pip': 'pip --version',
        'node': 'node --version',
        'npm': 'npm --version',
        'git': 'git --version'
    }
    
    missing = []
    for tool, command in requirements.items():
        result = run_command(command, check=False)
        if result.returncode != 0:
            missing.append(tool)
        else:
            print(f"✅ {tool}: {result.stdout.strip()}")
    
    if missing:
        print(f"❌ Missing prerequisites: {', '.join(missing)}")
        print("Please install the missing tools and run setup again.")
        sys.exit(1)
    
    print("✅ All prerequisites satisfied!")

def setup_python_environment():
    """Setup Python virtual environment and install dependencies"""
    print("\n🐍 Setting up Python environment...")
    
    # Create virtual environment
    if not os.path.exists('venv'):
        print("Creating virtual environment...")
        run_command('python -m venv venv')
    
    # Activate virtual environment and install dependencies
    if os.name == 'nt':  # Windows
        pip_path = 'venv\\Scripts\\pip'
        python_path = 'venv\\Scripts\\python'
    else:  # Unix/Linux/macOS
        pip_path = 'venv/bin/pip'
        python_path = 'venv/bin/python'
    
    print("Installing Python dependencies...")
    run_command(f'{pip_path} install --upgrade pip')
    run_command(f'{pip_path} install -r requirements.txt')
    
    # Install development dependencies if available
    if os.path.exists('requirements-dev.txt'):
        print("Installing development dependencies...")
        run_command(f'{pip_path} install -r requirements-dev.txt')
    
    print("✅ Python environment setup complete!")

def setup_frontend():
    """Setup frontend dependencies"""
    print("\n⚛️ Setting up frontend...")
    
    frontend_dir = Path('frontend')
    if not frontend_dir.exists():
        print("❌ Frontend directory not found!")
        return
    
    print("Installing Node.js dependencies...")
    run_command('npm install', cwd=frontend_dir)
    
    print("✅ Frontend setup complete!")

def setup_database():
    """Setup database"""
    print("\n🗄️ Setting up database...")
    
    # Run database migration
    if os.path.exists('scripts/migrate_database.py'):
        if os.name == 'nt':  # Windows
            python_path = 'venv\\Scripts\\python'
        else:  # Unix/Linux/macOS
            python_path = 'venv/bin/python'
        
        print("Running database migration...")
        run_command(f'{python_path} scripts/migrate_database.py')
    
    print("✅ Database setup complete!")

def setup_environment():
    """Setup environment configuration"""
    print("\n⚙️ Setting up environment configuration...")
    
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            print("Creating .env file from template...")
            shutil.copy('.env.example', '.env')
            print("📝 Please edit .env file with your configuration!")
        else:
            print("❌ .env.example not found!")
    else:
        print("✅ .env file already exists!")

def run_tests():
    """Run tests to verify setup"""
    print("\n🧪 Running tests...")
    
    if os.name == 'nt':  # Windows
        python_path = 'venv\\Scripts\\python'
    else:  # Unix/Linux/macOS
        python_path = 'venv/bin/python'
    
    # Run backend tests
    if os.path.exists('scripts/test_enhanced_api.py'):
        print("Running backend tests...")
        result = run_command(f'{python_path} scripts/test_enhanced_api.py', check=False)
        if result.returncode == 0:
            print("✅ Backend tests passed!")
        else:
            print("⚠️ Backend tests failed - check configuration")
    
    # Run frontend tests
    frontend_dir = Path('frontend')
    if frontend_dir.exists():
        print("Running frontend tests...")
        result = run_command('npm test -- --watchAll=false', cwd=frontend_dir, check=False)
        if result.returncode == 0:
            print("✅ Frontend tests passed!")
        else:
            print("⚠️ Frontend tests failed - check configuration")

def print_next_steps():
    """Print next steps for the user"""
    print("\n🎉 Setup complete! Next steps:")
    print("\n1. Configure your environment:")
    print("   - Edit .env file with your settings")
    print("   - Update SECRET_KEY with a secure value")
    print("   - Configure database settings if needed")
    
    print("\n2. Start the development servers:")
    print("   Backend:")
    if os.name == 'nt':  # Windows
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("   python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000")
    
    print("\n   Frontend (in a new terminal):")
    print("   cd frontend")
    print("   npm start")
    
    print("\n3. Access the application:")
    print("   - Frontend: http://localhost:3000")
    print("   - Backend API: http://localhost:8000")
    print("   - API Docs: http://localhost:8000/docs")
    
    print("\n4. For production deployment:")
    print("   - See docs/DEPLOYMENT.md")
    print("   - Use Docker: docker-compose up --build")
    
    print("\n📚 Documentation:")
    print("   - README.md - Project overview")
    print("   - docs/API.md - API documentation")
    print("   - docs/CONTRIBUTING.md - Contribution guidelines")
    print("   - docs/DEPLOYMENT.md - Deployment guide")

def main():
    """Main setup function"""
    print("🏥 HealthTwin AI Setup Script")
    print("=" * 40)
    
    # Change to project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)
    
    try:
        check_prerequisites()
        setup_environment()
        setup_python_environment()
        setup_frontend()
        setup_database()
        run_tests()
        print_next_steps()
        
    except KeyboardInterrupt:
        print("\n❌ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
