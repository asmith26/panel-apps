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
convert-panel-to-web:                        ## Generates a static web application from panel (via pyodide)
	panel convert app.py --to pyodide-worker --out ../docs/hello_pyodide

serve-local-panel:                           ## Launch a local panel server (with debug options)
	panel serve app.py --autoreload --show


## Web
local-web-server:                            ## Launch a local web server
	cd .. && python3 -m http.server
	# and navigate to http://0.0.0.0:8000/docs/hello_pyodide/app.html
