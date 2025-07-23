"""
Project cleanup script to remove unwanted files and organize the structure
"""
import os
import shutil
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def remove_pycache_files():
    """Remove all __pycache__ directories"""
    logger.info("Removing __pycache__ directories...")
    
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(pycache_path)
                logger.info(f"Removed: {pycache_path}")
            except Exception as e:
                logger.warning(f"Could not remove {pycache_path}: {e}")

def create_gitignore():
    """Create a comprehensive .gitignore file"""
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project specific
logs/
test_images/
test_results/
uploads/*.jpg
uploads/*.png
uploads/*.jpeg
*.db
backups/
enhanced_ocr_config.json

# Node modules (frontend)
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local
"""
    
    try:
        with open('.gitignore', 'w') as f:
            f.write(gitignore_content)
        logger.info("Created .gitignore file")
    except Exception as e:
        logger.error(f"Could not create .gitignore: {e}")

def organize_project_structure():
    """Organize the project structure"""
    logger.info("Organizing project structure...")
    
    # Create necessary directories if they don't exist
    directories = [
        'logs',
        'test_images', 
        'test_results',
        'uploads'
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
                logger.info(f"Created directory: {directory}")
            except Exception as e:
                logger.warning(f"Could not create {directory}: {e}")
    
    # Create empty .gitkeep files in directories that should be tracked but empty
    gitkeep_dirs = ['logs', 'test_images', 'test_results']
    for directory in gitkeep_dirs:
        gitkeep_path = os.path.join(directory, '.gitkeep')
        if os.path.exists(directory) and not os.path.exists(gitkeep_path):
            try:
                with open(gitkeep_path, 'w') as f:
                    f.write('')
                logger.info(f"Created .gitkeep in {directory}")
            except Exception as e:
                logger.warning(f"Could not create .gitkeep in {directory}: {e}")

def clean_uploads_directory():
    """Clean old uploaded files"""
    logger.info("Cleaning uploads directory...")
    
    uploads_dir = 'uploads'
    if os.path.exists(uploads_dir):
        for filename in os.listdir(uploads_dir):
            if filename.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                file_path = os.path.join(uploads_dir, filename)
                try:
                    os.remove(file_path)
                    logger.info(f"Removed upload: {filename}")
                except Exception as e:
                    logger.warning(f"Could not remove {filename}: {e}")

def main():
    """Main cleanup function"""
    logger.info("Starting project cleanup...")
    logger.info("=" * 50)
    
    # Remove cache files
    remove_pycache_files()
    
    # Create .gitignore
    create_gitignore()
    
    # Organize structure
    organize_project_structure()
    
    # Clean uploads (optional)
    response = input("Do you want to clean old uploaded files? (y/n): ")
    if response.lower() == 'y':
        clean_uploads_directory()
    
    logger.info("=" * 50)
    logger.info("Project cleanup completed!")
    logger.info("\nCleaned project structure:")
    logger.info("✓ Removed __pycache__ directories")
    logger.info("✓ Created .gitignore file")
    logger.info("✓ Organized directory structure")
    logger.info("✓ Added .gitkeep files for empty directories")
    
    logger.info("\nFinal project structure:")
    logger.info("├── app/                 # Main application")
    logger.info("│   ├── ml_pipeline/     # Enhanced OCR engines")
    logger.info("│   ├── services/        # OCR services")
    logger.info("│   ├── main.py          # Enhanced server")
    logger.info("│   └── simple_main.py   # Basic server")
    logger.info("├── frontend/            # React frontend")
    logger.info("├── scripts/             # Utility scripts")
    logger.info("├── docs/                # Documentation")
    logger.info("├── docker/              # Docker configuration")
    logger.info("├── uploads/             # Uploaded files")
    logger.info("├── logs/                # Log files")
    logger.info("├── requirements.txt     # Python dependencies")
    logger.info("└── start_enhanced_server.py  # Server startup")

if __name__ == "__main__":
    main()
