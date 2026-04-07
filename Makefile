PYTHON ?= python3
TOPO ?= clab/topology.clab.yml
EXPECTED ?= automation/expected_state.yml

LAB_NAME ?= mini-fabric-lab

deploy:
	sudo containerlab deploy -t $(TOPO)

destroy:
	sudo containerlab destroy -t $(TOPO) --cleanup

healthcheck:
	$(PYTHON) automation/healthcheck.py --lab-name $(LAB_NAME) --expected $(EXPECTED)

collect:
	$(PYTHON) automation/collect_evidence.py --lab-name $(LAB_NAME) --expected $(EXPECTED)

test: healthcheck
