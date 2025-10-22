# API Configuration

This folder contains API key configuration files.

## Setup

1. Copy `keys.example.py` to `keys.py`:
   ```bash
   cp api/keys.example.py api/keys.py
   ```

2. Edit `api/keys.py` and replace `sk-proj-xxxx` with your actual OpenAI API key:
   ```python
   OPENAI_API_KEY = "sk-proj-your-actual-key-here"
   ```

3. Get your API key from: https://platform.openai.com/api-keys

## Security

⚠️ **Important**: The `keys.py` file is listed in `.gitignore` to prevent accidental commits of your API key. Never commit this file to version control!

## Files

- `keys.example.py` - Template file (committed to git)
- `keys.py` - Your actual API keys (ignored by git)
- `__init__.py` - Python package file

