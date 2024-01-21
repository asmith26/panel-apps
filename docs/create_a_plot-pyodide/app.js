importScripts("https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.js");

function sendPatch(patch, buffers, msg_id) {
  self.postMessage({
    type: 'patch',
    patch: patch,
    buffers: buffers
  })
}

async function startApplication() {
  console.log("Loading pyodide!");
  self.postMessage({type: 'status', msg: 'Loading pyodide'})
  self.pyodide = await loadPyodide();
  self.pyodide.globals.set("sendPatch", sendPatch);
  console.log("Loaded!");
  await self.pyodide.loadPackage("micropip");
  const env_spec = ['https://cdn.holoviz.org/panel/wheels/bokeh-3.3.3-py3-none-any.whl', 'https://cdn.holoviz.org/panel/1.3.6/dist/wheels/panel-1.3.6-py3-none-any.whl', 'pyodide-http==0.2.1', 'matplotlib', 'requests']
  for (const pkg of env_spec) {
    let pkg_name;
    if (pkg.endsWith('.whl')) {
      pkg_name = pkg.split('/').slice(-1)[0].split('-')[0]
    } else {
      pkg_name = pkg
    }
    self.postMessage({type: 'status', msg: `Installing ${pkg_name}`})
    try {
      await self.pyodide.runPythonAsync(`
        import micropip
        await micropip.install('${pkg}');
      `);
    } catch(e) {
      console.log(e)
      self.postMessage({
	type: 'status',
	msg: `Error while installing ${pkg_name}`
      });
    }
  }
  console.log("Packages loaded!");
  self.postMessage({type: 'status', msg: 'Executing code'})
  const code = `
  
import asyncio

from panel.io.pyodide import init_doc, write_doc

init_doc()

# Adapted from https://huggingface.co/spaces/ahuang11/tweak-mpl-chat/raw/main/app.py
# Blog: https://blog.holoviz.org/posts/tweak-mpl-chat/ (also https://huggingface.co/blog/sophiamyang/tweak-mpl-chat)
import json
import re

import panel as pn
import requests
from panel.io.mime_render import exec_with_return
import matplotlib
matplotlib.use('agg')  # required for pyodide

pn.extension("codeeditor", sizing_mode="stretch_width")

SYSTEM_MESSAGE = "You are a renowned data visualization expert " \
        "with a strong background in matplotlib. " \
        "Your primary goal is to assist the user " \
        "to edit the code based on a user request " \
        "using best practices. Simply provide code " \
        "in code fences (\`\`\`python). You must have \`fig\` " \
        "as the last line of code and never call fig.close()"
INITIAL_CODE = """
import numpy as np
import matplotlib
matplotlib.use('agg')  # required for pyodide
import matplotlib.pyplot as plt

fig = plt.figure()
ax = plt.axes(title="Plot Title", xlabel="X Label", ylabel="Y Label")

x = np.linspace(1, 10)
y = np.sin(x)
z = np.cos(x)
c = np.log(x)

ax.plot(x, y, c="blue", label="sin")
ax.plot(x, z, c="orange", label="cos")

img = ax.scatter(x, c, c=c, label="log")
plt.colorbar(img, label="Colorbar")
plt.legend()

# must have fig at the end!
fig
""".strip()


def callback(content: str, user: str, instance: pn.chat.ChatInterface):
# async def callback(content: str, user: str, instance: pn.chat.ChatInterface):
    # return "test"
    in_message = f"{content}\\n\\n\`\`\`python\\n{code_editor.value}\`\`\`"
    data = {
        "model": "mistral",
        "system": SYSTEM_MESSAGE,
        "prompt": in_message,
        "stream": True,
        "options": {
            'temperature': 0,
        },
    }

    response = requests.post("https://asmith26--ollama-server-create-asgi.modal.run/api/generate", json=data)
    responses = response.content.decode("utf-8").strip().split("\\n")

    # stream LLM tokens
    message = ""
    for line in responses:
        parsed = json.loads(line)
        message += parsed["response"]
        yield message

    # extract code
    llm_code = re.findall(r"\`\`\`python\\n(.*)\\n\`\`\`", message, re.DOTALL)[0]
    if llm_code.splitlines()[-1].strip() != "fig":
        llm_code += "\\nfig"
    code_editor.value = llm_code


def update_plot(event):
    matplotlib_pane.object = exec_with_return(event.new)


# instantiate widgets and panes
chat_interface = pn.chat.ChatInterface(
    callback=callback,
    show_clear=False,
    show_undo=False,
    show_button_name=False,
    message_params=dict(
        show_reaction_icons=False,
        show_copy_icon=False,
    ),
    height=500,
    callback_exception="verbose",
)
matplotlib_pane = pn.pane.Matplotlib(
    exec_with_return(INITIAL_CODE),
    sizing_mode="stretch_both",
    tight=True,
)
code_editor = pn.widgets.CodeEditor(
    value=INITIAL_CODE,
    language="python",
    sizing_mode="stretch_both",
)

# watch for code changes
code_editor.param.watch(update_plot, "value")

# lay them out
tabs = pn.Tabs(
    ("Plot", matplotlib_pane),
    ("Code", code_editor),
)

sidebar = [chat_interface, pn.pane.Markdown("#### Examples \\n"
                                            "- Please add gridlines to this plot.")]
main = [tabs]
template = pn.template.FastListTemplate(
    sidebar=sidebar,
    main=main,
    sidebar_width=500,
    main_layout=None,
    accent_base_color="#fd7000",
    header_background="#fd7000",
    title="Create a plot"
)
template.servable()


await write_doc()
  `

  try {
    const [docs_json, render_items, root_ids] = await self.pyodide.runPythonAsync(code)
    self.postMessage({
      type: 'render',
      docs_json: docs_json,
      render_items: render_items,
      root_ids: root_ids
    })
  } catch(e) {
    const traceback = `${e}`
    const tblines = traceback.split('\n')
    self.postMessage({
      type: 'status',
      msg: tblines[tblines.length-2]
    });
    throw e
  }
}

self.onmessage = async (event) => {
  const msg = event.data
  if (msg.type === 'rendered') {
    self.pyodide.runPythonAsync(`
    from panel.io.state import state
    from panel.io.pyodide import _link_docs_worker

    _link_docs_worker(state.curdoc, sendPatch, setter='js')
    `)
  } else if (msg.type === 'patch') {
    self.pyodide.globals.set('patch', msg.patch)
    self.pyodide.runPythonAsync(`
    state.curdoc.apply_json_patch(patch.to_py(), setter='js')
    `)
    self.postMessage({type: 'idle'})
  } else if (msg.type === 'location') {
    self.pyodide.globals.set('location', msg.location)
    self.pyodide.runPythonAsync(`
    import json
    from panel.io.state import state
    from panel.util import edit_readonly
    if state.location:
        loc_data = json.loads(location)
        with edit_readonly(state.location):
            state.location.param.update({
                k: v for k, v in loc_data.items() if k in state.location.param
            })
    `)
  }
}

startApplication()