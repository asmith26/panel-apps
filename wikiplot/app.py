# https://panel.holoviz.org/how_to/notebook/examples/hello_world.html

import panel as pn

pn.extension(template='fast')

import matplotlib.pyplot as plt
import numpy as np

def create_voltage_figure(figsize=(4,3)):
       t = np.arange(0.0, 2.0, 0.01)
       s = 1 + np.sin(2 * np.pi * t)

       fig, ax = plt.subplots(figsize=figsize)
       ax.plot(t, s)

       ax.set(xlabel='time (s)', ylabel='voltage (mV)',
              title='Voltage')
       ax.grid()

       plt.close(fig) # CLOSE THE FIGURE!
       return fig

pn.pane.Matplotlib(create_voltage_figure(), dpi=144, tight=True)
pn.Row(pn.pane.Matplotlib(create_voltage_figure(), dpi=144, tight=True)).servable()
