#!/usr/bin/env python3
import re

# Read pyproject.toml
with open("pyproject.toml", "r") as f:
    content = f.read()

# Find version and update build number
version_pattern = r'version = "([\d]+)\.([\d]+)\.([\d]+)\.([\d]+)"'
version_match = re.search(version_pattern, content)

if version_match:
    major, minor, patch, build = version_match.groups()
    new_build = str(int(build) + 1)
    new_version = f"{major}.{minor}.{patch}.{new_build}"
    new_content = re.sub(version_pattern, f'version = "{new_version}"', content)
    
    # Write updated content back
    with open("pyproject.toml", "w") as f:
        f.write(new_content)
    
    print(f"Updated version to {new_version}")
else:
    print("Version pattern not found in pyproject.toml")