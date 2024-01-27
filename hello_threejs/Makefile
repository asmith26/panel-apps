help:                                        ## Show help docs
	@sed -ne '/@sed/!s/## //p' $(MAKEFILE_LIST)

env-create:                                  ## Create mamba env
	mamba create -n threejs python=3.11

#env-update:                                  ## Install/update pip requirements
#	pip install -r ../create_a_plot/requirements.txt
#	pip install modal

#pip-freeze:                                  ## Freeze pip requirements
#	echo "Please freeze requirements via ../create_a_plot/Makefile"


# Panel
#convert-panel-to-web:                        ## Generates a static web application from panel (via pyodide)
#	panel convert app.py --to pyodide-worker --out ../docs/create_a_plot-pyodide

serve-local-panel:                           ## Launch a local panel server (with debug options)
	panel serve app.py --autoreload --show


# Web
#local-web-server:                            ## Launch a local web server
#	echo "Navigate to http://0.0.0.0:8000/docs/create_a_plot-pyodide/app.html"
#	cd .. && python3 -m http.server


## Modal
#modal-serve:                                 ## Launch a modal server that watches files and updates app on change
#	modal serve ../utils/modal_app.py
#
#modal-deploy:                                ## Deploys application to modal
#	modal deploy ../utils/modal_app.py
