help:                                        ## Show help docs
	@sed -ne '/@sed/!s/## //p' $(MAKEFILE_LIST)

env-create:                                  ## Create mamba env
	mamba env create -f environment-from_history.yml

env-create-from-lock:                        ## Create mamba env (via lock)
	mamba env create -f environment.yml

env-export:                                  ## Export mamba env
	mamba env export > environment.yml
	mamba env export --from-history > environment-from_history.yml


## Panel
convert-panel-to-webassembly:
	# mamba install panel
	panel convert hello_world/app.py --to pyodide-worker --out docs/hello_world

serve-local-panel:
	python3 -m http.server
	# and navigate to http://0.0.0.0:8000/panel_apps/hello_world/hello_world.html
