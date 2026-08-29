.PHONY: help dev test build release clean

help:
	@echo "Available Makefile targets:"
	@echo "  make dev                 - Sync dev and optional dependencies"
	@echo "  make test                - Run pytest test suite"
	@echo "  make build               - Build distribution packages in dist/"
	@echo "  make release v=0.2.0     - Bump version, commit, tag v0.2.0, and push"

dev:
	uv sync --extra dev --extra openai

test:
	uv run --extra dev --extra openai pytest

build: clean
	uv build

clean:
	rm -rf dist/ build/ *.egg-info

release: test
ifndef v
	$(error Usage: make release v=X.Y.Z)
endif
	@echo "Bumping version to $(v)..."
	@python3 -c "import re; p='src/zorveus/_version.py'; content=open(p).read(); open(p,'w').write(re.sub(r'__version__\s*=\s*\".*?\"', f'__version__ = \"$(v)\"', content))"
	uv build
	git add src/zorveus/_version.py pyproject.toml
	git commit -m "release: v$(v)"
	git tag -a "v$(v)" -m "Release v$(v)"
	git push origin main --tags
	@echo "Release v$(v) pushed! GitHub Actions will publish to PyPI."
