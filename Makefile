PYTHON := /home/alex/git_repos/isaacsim/_build/linux-x86_64/release/python.sh

field:
	$(PYTHON) sim/generate_field.py

field-gui:
	$(PYTHON) sim/generate_field.py --no-headless

test:
	$(PYTHON) -m pytest tests/

.PHONY: field field-gui test
