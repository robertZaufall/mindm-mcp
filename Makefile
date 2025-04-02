.PHONY: clean build update-version docs

# Default target
all: clean update-version build install llms

# Clean the dist folder
clean:
	rm -rf dist/*

# Update version in pyproject.toml (increment last digit)
update-version:
	@python update_version.py

# Build the package
build:
	uv run -m build

# Install the package
install:
	uv pip install -e .

# Generate documentation
llms:
	uv pip install gitingest
	gitingest . -o llms.txt -i "pyproject.toml,update_version.py,LICENSE,README.md,examples/*,mindm_mcp/*,assets/*.json" -e "llms.txt,mindm_mcp/__pycache__,mindm_mcp/.DS_Store,mindmap/.DS.Store,assets/archive/*"

# Create a release on Github
release:
	@if [ -z "$$VERSION" ]; then \
		echo "Error: VERSION is required. Use 'make release VERSION=x.x.x'"; \
		exit 1; \
	fi
	@echo "Creating release v$$VERSION..."
	git tag -a v$$VERSION -m "Release v$$VERSION"
	git push origin v$$VERSION
	@echo "\nRelease v$$VERSION created."

# Call inspector
inspector:
	uv run --with mindm --with fastmcp --with markdown-it-py mcp dev mindm_mcp/server.py
# npx @modelcontextprotocol/inspector uv --directory . run 

# Help
help:
	@echo "Available targets:"
	@echo "  all            - Run clean, update-version, build, and docs"
	@echo "  clean          - Remove contents of dist folder"
	@echo "  update-version - Increment build number in pyproject.toml"
	@echo "  build          - Build the package with python -m build"
	@echo "  llms           - Generate one file including all code and relevant files for llms"
	@echo "  release        - Create a release on Github. Use 'make release VERSION=x.x.x'"
	@echo "  inspector      - Run inspector"
	@echo "  help           - Show this help message"
