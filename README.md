### Export requirements to requirements.txt
```bash
uv export --format requirements-txt > requirements.txt
```

## TODOs
* [ ] Add method for agent to work an already existing folder
* [ ] Use persistent vector database based on Docker
* [ ] Try integration with VSCode. See https://pascoal.net/2024/10/31/gh-copilot-extensions-vscode-creating-extension/
* [ ] Enhance document generation to include metadata like links to the original source and edit button
* [ ] Use structured output for agent
* [ ] Improve how agent derives queries to use with vector database
* [ ] Architecture: VS Code extension => a2a => agent (cloud hosted) => vector database
* [ ] See JS a2a protocol client: https://github.com/a2aproject/a2a-js