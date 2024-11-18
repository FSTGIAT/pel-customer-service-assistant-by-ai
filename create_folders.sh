#!/bin/bash

# Create the 'app' directory structure and required files
mkdir -p app/api/routes
mkdir -p app/core
mkdir -p app/db
mkdir -p app/services
mkdir -p app/utils

# Create the necessary files in 'app' directory
touch app/__init__.py
touch app/main.py
touch app/config.py

# Create files for 'api' directory
touch app/api/__init__.py
touch app/api/routes/__init__.py
touch app/api/routes/chat.py
touch app/api/routes/customer.py

# Create files for 'core' directory
touch app/core/__init__.py
touch app/core/security.py
touch app/core/config.py

# Create files for 'db' directory
touch app/db/__init__.py
touch app/db/session.py
touch app/db/models.py

# Create files for 'services' directory
touch app/services/__init__.py
touch app/services/claude_service.py
touch app/services/pdf_service.py
touch app/services/cache_service.py

# Create files for 'utils' directory
touch app/utils/__init__.py
touch app/utils/logging.py

# Create the 'tests' directory and the __init__.py file
mkdir -p tests
touch tests/__init__.py

# Create the .env file
touch .env

# Create the .gitignore file
touch .gitignore

# Create the requirements.txt file
touch requirements.txt

# Output success message
echo "Directory structure has been created in the current directory."

