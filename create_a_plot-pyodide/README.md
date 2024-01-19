This provides an example of deploying the [create_a_plot](../create_a_plot) Panel application to GitHub Pages via Pyodide.

To test locally, run:

```bash
$ make env-create
$ mamba activate create_a_plot-pyodide
$ make env-update

TODO DEPLOY MODAL

$ make convert-panel-to-web
$ make local-web-server  # and navigate to http://0.0.0.0:8000/docs/create_a_plot-pyodide/app.html
```

Once happy, git commit and push to GitHub. To enable GitHub Pages, go to `Settings > Pages`. In the 
**Build and deployment** section, set **Branch** to `main`   and folder to `/docs`:

![Deploying GitHub Pages](../images/deploying_github_pages.png)

GitHub Actions will now deploy to GitHub Pages automatically on a `git push` to 
https://asmith26.github.io/panel-apps/create_a_plot-pyodide/app.html
