help:                                        ## Show help docs
	@sed -ne '/@sed/!s/## //p' $(MAKEFILE_LIST)

env-create:                                  ## Create mamba env
	mamba create -n create_a_plot python=3.11

env-update:                                  ## Install/update pip requirements
	pip install -r requirements.txt
	pip install modal

pip-freeze:                                  ## Freeze pip requirements
	pip freeze > requirements.txt


# Panel
serve-local-panel:                           ## Launch a local panel server (with debug options)
	panel serve app.py --autoreload --show


# Modal
modal-serve:                                 ## Launch a modal server that watches files and updates app on change
	modal serve ../utils/modal_app.py

modal-deploy:                                ## Deploys application to modal
	modal deploy ../utils/modal_app.py
