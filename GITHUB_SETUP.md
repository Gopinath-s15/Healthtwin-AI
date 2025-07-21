# GitHub Repository Setup Guide

This guide provides step-by-step instructions for setting up the HealthTwin AI project in your new GitHub repository.

## Prerequisites

1. **GitHub Account**: Ensure you have a GitHub account
2. **Git Installed**: Make sure Git is installed on your system
3. **Repository Created**: You should have created the "Healthtwin-AI" repository on GitHub

## Step 1: Update Repository URL References

**Replace `yourusername` with your actual GitHub username** in the following files:

### Files to Update:
- `README.md`
- `docs/API.md`
- `docs/CONTRIBUTING.md`
- `docs/DEPLOYMENT.md`

### Find and Replace:
```
Find: yourusername/Healthtwin-AI
Replace: YOUR_ACTUAL_USERNAME/Healthtwin-AI
```

**Example**: If your GitHub username is `johnsmith`, replace:
- `https://github.com/yourusername/Healthtwin-AI`
- With: `https://github.com/johnsmith/Healthtwin-AI`

## Step 2: Git Repository Configuration

### Option A: If this is a completely new repository

```bash
# Navigate to your project directory
cd "c:\Users\virat\OneDrive\Desktop\HealthTwin - Backend"

# Initialize Git repository (if not already done)
git init

# Add your GitHub repository as remote origin
git remote add origin https://github.com/YOUR_USERNAME/Healthtwin-AI.git

# Verify remote configuration
git remote -v
```

### Option B: If you need to change the remote URL

```bash
# Navigate to your project directory
cd "c:\Users\virat\OneDrive\Desktop\HealthTwin - Backend"

# Remove existing remote (if it points to the old repository)
git remote remove origin

# Add new remote origin
git remote add origin https://github.com/YOUR_USERNAME/Healthtwin-AI.git

# Verify remote configuration
git remote -v
```

## Step 3: Prepare Files for Initial Commit

### Check Git Status
```bash
# See what files are ready to be committed
git status
```

### Stage All Files
```bash
# Add all files to staging area
git add .

# Or add specific files/directories
git add README.md
git add app/
git add frontend/
git add docs/
git add scripts/
git add docker/
git add requirements.txt
git add .env.example
git add .gitignore
git add LICENSE
git add docker-compose.yml
```

### Verify Staged Files
```bash
# Check what's staged for commit
git status
```

## Step 4: Create Initial Commit

```bash
# Create initial commit with descriptive message
git commit -m "feat: initial commit - HealthTwin AI v2.0.0

- Enhanced FastAPI backend with authentication system
- React frontend with modern UI/UX
- JWT-based patient and doctor authentication
- Role-based access control
- Comprehensive API documentation
- Docker deployment configuration
- Database migration scripts
- Production-ready deployment guides

Features:
- Patient registration and login
- Doctor interface for patient management
- Secure file upload for prescriptions
- Medical timeline tracking
- Enhanced database schema
- Comprehensive testing suite
- HIPAA-ready architecture"
```

## Step 5: Set Up Branch Structure

```bash
# Create and switch to develop branch
git checkout -b develop

# Push develop branch to remote
git push -u origin develop

# Switch back to main branch
git checkout main
```

## Step 6: Push to GitHub

### Push Main Branch
```bash
# Push main branch to GitHub
git push -u origin main
```

### Push All Branches
```bash
# Push all branches
git push --all origin
```

## Step 7: Create Release Tag

```bash
# Create annotated tag for version 2.0.0
git tag -a v2.0.0 -m "Release v2.0.0: Enhanced HealthTwin AI with Authentication

Major Features:
- Enhanced patient and doctor authentication system
- JWT-based security with role-based access control
- Comprehensive API documentation
- Docker deployment support
- Production-ready configuration
- Enhanced database schema with migration support
- Modern React frontend with improved UX
- Comprehensive testing suite

This release marks the transition from basic medical records management 
to a full-featured, secure healthcare platform ready for production use."

# Push tags to remote
git push origin --tags
```

## Step 8: Verify Repository Setup

### Check Remote Configuration
```bash
# Verify remote is correctly set
git remote -v
# Should show:
# origin  https://github.com/YOUR_USERNAME/Healthtwin-AI.git (fetch)
# origin  https://github.com/YOUR_USERNAME/Healthtwin-AI.git (push)
```

### Check Branch Status
```bash
# Check current branch and status
git branch -a
git status
```

### Verify on GitHub
1. Go to `https://github.com/YOUR_USERNAME/Healthtwin-AI`
2. Verify all files are present
3. Check that the README.md displays correctly
4. Verify the release tag v2.0.0 is created

## Step 9: Configure Repository Settings (Optional)

### On GitHub.com:

1. **Repository Description**: Add a description like "Intelligent Medical Records Platform with AI-powered features"

2. **Topics/Tags**: Add relevant topics:
   - `healthcare`
   - `medical-records`
   - `fastapi`
   - `react`
   - `jwt-authentication`
   - `python`
   - `javascript`
   - `docker`
   - `ai`
   - `hipaa`

3. **Branch Protection** (Recommended for production):
   - Go to Settings → Branches
   - Add rule for `main` branch
   - Enable "Require pull request reviews before merging"
   - Enable "Require status checks to pass before merging"

4. **Issues and Discussions**:
   - Enable Issues for bug reports and feature requests
   - Enable Discussions for community interaction

## Step 10: Update Documentation URLs

After pushing to GitHub, update any remaining placeholder URLs in your documentation with the actual repository URL.

## Troubleshooting

### Common Issues:

1. **Authentication Error**:
   ```bash
   # If you get authentication errors, you may need to use a personal access token
   # Go to GitHub Settings → Developer settings → Personal access tokens
   # Generate a new token and use it as your password
   ```

2. **Large File Warning**:
   ```bash
   # If you get warnings about large files, check .gitignore
   # Make sure node_modules/, uploads/, and *.db files are ignored
   ```

3. **Remote Already Exists**:
   ```bash
   # If remote already exists, update it instead
   git remote set-url origin https://github.com/YOUR_USERNAME/Healthtwin-AI.git
   ```

4. **Permission Denied**:
   ```bash
   # Make sure you have write access to the repository
   # Check if you're using the correct username and repository name
   ```

## Next Steps

1. **Set up CI/CD** (Optional):
   - Create `.github/workflows/` directory
   - Add GitHub Actions for automated testing and deployment

2. **Configure Branch Protection**:
   - Protect main branch
   - Require pull request reviews

3. **Add Contributors**:
   - Invite team members to the repository
   - Set appropriate permissions

4. **Create Issues and Milestones**:
   - Add issues for planned features
   - Create milestones for version planning

## Example Complete Setup Commands

Here's a complete example assuming your GitHub username is `johnsmith`:

```bash
# Navigate to project directory
cd "c:\Users\virat\OneDrive\Desktop\HealthTwin - Backend"

# Initialize and configure Git
git init
git remote add origin https://github.com/johnsmith/Healthtwin-AI.git

# Stage and commit all files
git add .
git commit -m "feat: initial commit - HealthTwin AI v2.0.0"

# Create and push branches
git push -u origin main
git checkout -b develop
git push -u origin develop
git checkout main

# Create and push release tag
git tag -a v2.0.0 -m "Release v2.0.0: Enhanced HealthTwin AI with Authentication"
git push origin --tags

# Verify setup
git remote -v
git branch -a
```

## Support

If you encounter any issues during setup:

1. Check the [Git documentation](https://git-scm.com/doc)
2. Review [GitHub's help documentation](https://docs.github.com/)
3. Create an issue in the repository for project-specific problems

---

**Remember to replace `YOUR_USERNAME` with your actual GitHub username throughout this process!**
