# Adapted from https://github.com/asmith26/panel-apps/blob/main/create_a_plot-pyodide/app.py
# (which in turn is based on from https://huggingface.co/spaces/ahuang11/tweak-mpl-chat/raw/main/app.py)
import json
import re

import panel as pn
import requests
from panel.io.mime_render import exec_with_return

pn.extension("codeeditor", sizing_mode="stretch_width")
SYSTEM_MESSAGE = "You are a renowned data visualization expert " \
        "with a strong background in matplotlib. " \
        "Your primary goal is to assist the user " \
        "in edit the code based on user request " \
        "using best practices. Simply provide code " \
        "in code fences (```python). You must start your " \
         " code with `import matplotlib\nmatplotlib.use('agg')\n`" \
        " and have `fig\n` as the last line of code"
INITIAL_CODE = """
<h1>This is an HTML pane</h1>

<code>
x = 5;<br>
y = 6;<br>
z = x + y;
</code>

<br>
<br>

<table>
  <tr>
    <th>Firstname</th>
    <th>Lastname</th> 
    <th>Age</th>
  </tr>
  <tr>
    <td>Jill</td>
    <td>Smith</td> 
    <td>50</td>
  </tr>
  <tr>
    <td>Eve</td>
    <td>Jackson</td> 
    <td>94</td>
  </tr>
</table>
""".strip()


def callback(content: str, user: str, instance: pn.chat.ChatInterface):
# async def callback(content: str, user: str, instance: pn.chat.ChatInterface):
    # return "test"
    in_message = f"{content}\n\n```python\n{code_editor.value}```"
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
    responses = response.content.decode("utf-8").strip().split("\n")

    # stream LLM tokens
    message = ""
    for line in responses:
        parsed = json.loads(line)
        message += parsed["response"]
        yield message

    # extract code
    llm_code = re.findall(r"```python\n(.*)```", message, re.DOTALL)[0]
    if llm_code.splitlines()[-1].strip() != "fig":
        llm_code += "\nfig\n"
    code_editor.value = llm_code


def update_plot(event):
    html_pane.object = event.new


# instantiate widgets and panes
chat_interface = pn.chat.ChatInterface(
    callback=callback,
    show_clear=True,
    show_undo=False,
    show_button_name=False,
    message_params=dict(
        show_reaction_icons=False,
        show_copy_icon=False,
    ),
    height=700,
    callback_exception="verbose",
)
styles = {
    'background-color': '#F6F6F6', 'border': '2px solid black',
    'border-radius': '5px', 'padding': '10px'
}
html_pane = pn.pane.HTML("""
<h1>This is an HTML pane</h1>

<code>
x = 5;<br>
y = 6;<br>
z = x + y;
</code>

<br>
<br>

<table>
  <tr>
    <th>Firstname</th>
    <th>Lastname</th> 
    <th>Age</th>
  </tr>
  <tr>
    <td>Jill</td>
    <td>Smith</td> 
    <td>50</td>
  </tr>
  <tr>
    <td>Eve</td>
    <td>Jackson</td> 
    <td>94</td>
  </tr>
</table>
""", styles=styles)
    # sizing_mode="stretch_both",
    # tight=True,
# )
code_editor = pn.widgets.CodeEditor(
    value=INITIAL_CODE,
    language="python",
    sizing_mode="stretch_both",
)

# watch for code changes
code_editor.param.watch(update_plot, "value")

# lay them out
tabs = pn.Tabs(
    ("Animation", html_pane),
    ("Code", code_editor),
)

sidebar = [chat_interface, pn.pane.Markdown("#### Examples \n"
                                            "- TODO")]
main = [tabs]
template = pn.template.FastListTemplate(
    sidebar=sidebar,
    main=main,
    sidebar_width=500,
    main_layout=None,
    accent_base_color="#fd7000",
    header_background="#fd7000",
    title="Create with three.js"
)
template.servable()
