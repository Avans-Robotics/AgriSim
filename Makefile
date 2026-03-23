PYTHON := /home/alex/git_repos/isaacsim/_build/linux-x86_64/release/python.sh
SIM    := sim/farm_manager.py

# ── Help ──────────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  agri-sim targets"
	@echo "  ────────────────────────────────────────────────────────────────"
	@echo "  Row-crop presets:"
	@echo "    make row                  5 rows × 10 cols, all plants, headless"
	@echo "    make row-gui              same, with Isaac Sim GUI"
	@echo "    make row ROWS=8 COLS=20   custom row/col count"
	@echo ""
	@echo "  Pixel-crop presets:"
	@echo "    make pixel                30 cm grid, all plants, headless"
	@echo "    make pixel-gui            same, with Isaac Sim GUI"
	@echo "    make pixel SPACING=0.20   custom grid spacing (metres)"
	@echo ""
	@echo "  Plant selection (any target):"
	@echo "    make row PLANTS=broccoli,lettuce"
	@echo "    make pixel PLANTS=carrot"
	@echo ""
	@echo "  Field size (any target):"
	@echo "    make row FIELD=30"
	@echo ""
	@echo "  Validation:"
	@echo "    make validate             100-frame headless test"
	@echo "    make test                 pytest suite"
	@echo ""
	@echo "  Or use:  ./run_sim.sh --help"
	@echo ""

# ── Configurable variables ────────────────────────────────────────────────────
ROWS    ?= 5
COLS    ?= 10
SPACING ?= 0.30
PLANTS  ?= broccoli,carrot,lettuce
FIELD   ?= 20
SEED    ?= 42

# ── Row-crop ──────────────────────────────────────────────────────────────────
row:
	$(PYTHON) $(SIM) --mode row \
	    --rows $(ROWS) --cols $(COLS) \
	    --plants "$(PLANTS)" --field-size $(FIELD) --seed $(SEED)

row-gui:
	$(PYTHON) $(SIM) --mode row --no-headless \
	    --rows $(ROWS) --cols $(COLS) \
	    --plants "$(PLANTS)" --field-size $(FIELD) --seed $(SEED)

# ── Pixel-crop ────────────────────────────────────────────────────────────────
pixel:
	$(PYTHON) $(SIM) --mode pixel \
	    --spacing $(SPACING) \
	    --plants "$(PLANTS)" --field-size $(FIELD) --seed $(SEED)

pixel-gui:
	$(PYTHON) $(SIM) --mode pixel --no-headless \
	    --spacing $(SPACING) \
	    --plants "$(PLANTS)" --field-size $(FIELD) --seed $(SEED)

# ── Validation ────────────────────────────────────────────────────────────────
validate:
	$(PYTHON) $(SIM) --test --plants "$(PLANTS)"

test:
	$(PYTHON) -m pytest tests/

# ── Legacy targets ────────────────────────────────────────────────────────────
field:
	$(PYTHON) sim/generate_field.py

field-gui:
	$(PYTHON) sim/generate_field.py --no-headless

.PHONY: help row row-gui pixel pixel-gui validate test field field-gui
