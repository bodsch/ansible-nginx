#
export TOX_SCENARIO  ?= default
export TOX_ANSIBLE   ?= ansible_9.5

# --------------------------------------------------------

# Alle Targets, die schlicht ein Skript in hooks/ aufrufen
HOOKS := doc prepare converge destroy verify test lint gh-clean

.PHONY: $(HOOKS)
.DEFAULT_GOAL := converge

# $@ expandiert zu dem Namen des gerade angeforderten Targets
$(HOOKS):
	@hooks/$@
