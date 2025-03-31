@ECHO OFF

pushd %~dp0

set SOURCEDIR=.

if exist dist\* del /s /q dist\* && if exist dist rmdir /s /q dist && mkdir dist
@python update_version.py
python -m build
uv pip install -e .

uv pip install gitingest
gitingest . -o llms.txt -i "pyproject.toml,update_version.py,LICENSE,README.md,examples/*,mindm_mcp/*" -e "llms.txt,mindm_mcp/__pycache__,mindm_mcp/.DS_Store,mindmap/.DS.Store"

:end
popd
