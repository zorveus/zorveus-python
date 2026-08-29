.PHONY: help dev test build release clean

VERSION ?= $(v)
UV := $(shell command -v uv 2>/dev/null || echo "$$HOME/.local/bin/uv")

help:
	@echo "Available Makefile targets:"
	@echo "  make dev                     - Sync dev and optional dependencies"
	@echo "  make test                    - Run pytest test suite"
	@echo "  make build                   - Build distribution packages in dist/"
	@echo "  make release VERSION=0.2.0   - Bump version, commit, tag v0.2.0, and push"

dev:
	$(UV) sync --extra dev --extra openai

test:
	$(UV) run --extra dev --extra openai pytest

build: clean
	$(UV) build

clean:
	rm -rf dist/ build/ *.egg-info

release: test
ifndef VERSION
	$(error Usage: make release VERSION=X.Y.Z)
endif
	@echo "Bumping version to $(VERSION)..."
	@python3 -c "import re; p='src/zorveus/_version.py'; content=open(p).read(); open(p,'w').write(re.sub(r'__version__\s*=\s*\".*?\"', f'__version__ = \"$(VERSION)\"', content))"
	$(UV) build
	git add src/zorveus/_version.py pyproject.toml Makefile .github/workflows/publish.yml
	@git diff-index --quiet HEAD || git commit -m "release: v$(VERSION)"
	git tag -f -a "v$(VERSION)" -m "Release v$(VERSION)"
	git push origin main --tags -f
	@echo "Release v$(VERSION) tagged and pushed! GitHub Actions will trigger PyPI publish."
