help:                                        ## Show help docs
	@sed -ne '/@sed/!s/## //p' $(MAKEFILE_LIST)

env-create:                                  ## Create mamba env and install pip requirements
	mamba create -n create_a_plot python=3.11
	pip install -r requirements.txt
	pip install modal

pip-freeze:                                  ## Freeze pip requirements
	pip freeze > requirements.txt

# Panel
serve-local-panel:                           ## Launch a local panel server (with debug options)
	panel serve app.py --autoreload --show


# Modal
modal-serve:                                 ## Launch a modal server that watches files and updates app on changes
	modal serve serve_modal.py

modal-deploy:                                ## Deploys application to modal
	modal deploy serve_modal.py
