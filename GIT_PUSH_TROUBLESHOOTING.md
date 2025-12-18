# Git Push Troubleshooting Guide

## Common Issues Preventing Git Push

### 1. **Merge Conflict in .gitignore**
Your `.gitignore` file has a merge conflict that needs to be resolved:
```
<<<<<<< HEAD
... (your changes)
=======
venv/
>>>>>>> fc843bf29042ed8b14667e04d78e9e7dbcc6d873
```

**Solution:** Resolve the merge conflict by keeping the complete version and removing the conflict markers.

### 2. **Large Files (ML Models)**
Your repository contains large `.pkl` model files that may exceed Git's file size limits:
- `MHOERS/ml_models/*.pkl` - Machine learning model files
- These files can be very large (often 10-100+ MB each)

**Solutions:**
- Add `*.pkl` to `.gitignore` if models can be regenerated
- Use Git LFS (Large File Storage) for model files
- Store models in cloud storage (S3, Google Drive) and download during setup

### 3. **Sensitive Data in settings.py**
Your `settings.py` contains:
- Database credentials (password: `Lxgiwyl123!`)
- Secret key
- These should NOT be committed to public repositories

**Solution:** Use environment variables or a separate `local_settings.py` file

### 4. **Files That Should Be Ignored**
Make sure these are in `.gitignore`:
- `venv/` - Virtual environment
- `__pycache__/` - Python cache
- `*.log` - Log files
- `ml_models/*.pkl` - ML model files (if large)
- `catboost_info/` - Training artifacts
- `MHOERS.backup` - Backup files
- `*.sql`, `*.sql.gz` - Database backups

## Step-by-Step Fix

### Step 1: Fix .gitignore Merge Conflict

1. Open `.gitignore`
2. Remove the conflict markers and keep the complete version:

```gitignore
# Python Virtual Environments
venv/
env/
ENV/
.venv/
env.bak/
venv.bak/

# Python
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
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Django
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal
/media
/staticfiles

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Environment variables
.env
.env.local
.env.*.local

# ML/AI specific - Training artifacts and cache
catboost_info/
*.tsv
tmp/
ml_models/*.pkl  # Add this if models are too large

# Jupyter Notebook
.ipynb_checkpoints

# pyenv
.python-version

# Backup files
*.bak
*.backup
MHOERS.backup/
MHOERS/backups/
*.sql
*.sql.gz

# OS specific
Thumbs.db
.DS_Store
```

### Step 2: Secure settings.py

Create a `local_settings.py` template and update `settings.py`:

**Create `MHOERS/MHOERS/local_settings.example.py`:**
```python
# Copy this file to local_settings.py and fill in your values
# DO NOT commit local_settings.py to Git

SECRET_KEY = 'your-secret-key-here'
DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'MHOERS',
        'USER': 'postgres',
        'PASSWORD': 'your-password-here',
        'HOST': 'localhost',
    }
}
```

**Update `MHOERS/MHOERS/settings.py` to use environment variables:**
```python
import os
from pathlib import Path

# ... existing code ...

# SECRET_KEY from environment or default (for development only)
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-%xu_imq+2k=@1!fp%4*34!_e+c%1&#z0xg!)ccg3$n8(n(k7x_')

# ... existing code ...

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'MHOERS'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Try to load local_settings.py if it exists (for development)
try:
    from .local_settings import *
except ImportError:
    pass
```

**Add to `.gitignore`:**
```gitignore
# Local settings (contains sensitive data)
local_settings.py
```

### Step 3: Handle Large Files

**Option A: Ignore ML Models (if they can be regenerated)**
Add to `.gitignore`:
```gitignore
# ML Models (too large for Git)
ml_models/*.pkl
ml_outputs/*.pkl
models/*.joblib
```

**Option B: Use Git LFS for models**
```bash
# Install Git LFS
git lfs install

# Track .pkl files with LFS
git lfs track "*.pkl"
git lfs track "*.joblib"

# Add .gitattributes
git add .gitattributes
```

### Step 4: Remove Already Committed Large/Sensitive Files

If you've already committed sensitive data or large files:

```bash
# Remove from Git history (BE CAREFUL - this rewrites history)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch MHOERS/MHOERS/settings.py" \
  --prune-empty --tag-name-filter cat -- --all

# Or use git-filter-repo (recommended, but needs installation)
# pip install git-filter-repo
# git filter-repo --path MHOERS/MHOERS/settings.py --invert-paths
```

### Step 5: Clean Up and Push

```bash
# Remove files that should be ignored
git rm -r --cached venv/
git rm -r --cached __pycache__/
git rm -r --cached *.log
git rm -r --cached ml_models/*.pkl  # If ignoring models

# Add the fixed .gitignore
git add .gitignore

# Commit changes
git commit -m "Fix .gitignore merge conflict and remove sensitive/large files"

# Add new remote (if pushing to different repository)
git remote add new-repo <repository-url>

# Push to new repository
git push new-repo main
# or
git push new-repo master
```

## Quick Checklist

- [ ] Fix `.gitignore` merge conflict
- [ ] Add `local_settings.py` to `.gitignore`
- [ ] Move sensitive data from `settings.py` to environment variables
- [ ] Add large files (`.pkl`, `.joblib`) to `.gitignore` or use Git LFS
- [ ] Remove already-committed sensitive/large files from Git history
- [ ] Test that sensitive files are not tracked: `git status`
- [ ] Create `README.md` with setup instructions
- [ ] Push to new repository

## Alternative: Start Fresh Repository

If the repository is too messy, you can start fresh:

```bash
# Create new repository
cd ..
git clone <new-repository-url> MHOERS-clean
cd MHOERS-clean

# Copy files (excluding ignored ones)
rsync -av --exclude='.git' --exclude='venv' --exclude='__pycache__' \
  ../MHOERS/ .

# Or on Windows PowerShell:
# Copy-Item -Path ..\MHOERS\* -Destination . -Recurse -Exclude venv,__pycache__

# Add and commit
git add .
git commit -m "Initial commit"
git push origin main
```

## Need Help?

If you're still having issues, check:
1. Repository size limits (GitHub: 100MB per file, 1GB per repo recommended)
2. Authentication (SSH keys or personal access tokens)
3. Branch protection rules on the remote repository
4. Network/firewall issues

