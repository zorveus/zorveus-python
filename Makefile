.PHONY: help dev test build release clean

# Accept both `make release 0.4.2` and `make release VERSION=0.4.2`.
ifeq ($(firstword $(MAKECMDGOALS)),release)
RELEASE_VERSION_GOAL := $(filter-out help dev test build release clean,$(word 2,$(MAKECMDGOALS)))
ifneq ($(RELEASE_VERSION_GOAL),)
.PHONY: $(RELEASE_VERSION_GOAL)
$(RELEASE_VERSION_GOAL):
	@:
endif
endif

VERSION ?= $(or $(v),$(RELEASE_VERSION_GOAL))
export RELEASE_VERSION = $(strip $(VERSION))
UV := $(shell command -v uv 2>/dev/null || echo "$$HOME/.local/bin/uv")

help:
	@echo "Available Makefile targets:"
	@echo "  make dev                     - Sync dev and optional dependencies"
	@echo "  make test                    - Run pytest test suite"
	@echo "  make build                   - Build distribution packages in dist/"
	@echo "  make release VERSION=0.2.0   - Bump version, commit, tag v0.2.0, and push"
	@echo "  make release 0.2.0           - Same release using a positional version"

dev:
	$(UV) sync --extra dev --extra openai

test:
	$(UV) run --extra dev --extra openai pytest

build: clean
	$(UV) build

clean:
	rm -rf dist/ build/ *.egg-info

release:
	@python3 -c 'import os, re, sys; re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", os.environ["RELEASE_VERSION"]) or sys.exit("Usage: make release VERSION=X.Y.Z (or make release X.Y.Z)")'
	$(MAKE) test
	@echo "Bumping version to $(VERSION)..."
	@python3 -c 'import os; from pathlib import Path; Path("src/zorveus/_version.py").write_text("__version__ = " + repr(os.environ["RELEASE_VERSION"]) + "\n")'
	$(UV) build
	git add src/zorveus/_version.py pyproject.toml Makefile .github/workflows/publish.yml
	@git diff-index --quiet HEAD || git commit -m "release: v$(VERSION)"
	git tag -f -a "v$(VERSION)" -m "Release v$(VERSION)"
	git push origin main --tags -f
	@echo "Release v$(VERSION) tagged and pushed! GitHub Actions will trigger PyPI publish."
