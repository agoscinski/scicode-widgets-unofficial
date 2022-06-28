import matplotlib.pyplot as plt

from ipywidgets import Output

import IPython.display

class CodeVisualizer:
    """CodeDemo supports this interface to execute code before and after the update of the visualizers. It does not inherit from ABC, because then it would conflict with the inheritence of widgets."""

    def before_visualizers_update(self):
        raise NotImplementedError("before_visualizers_update has not been implemented.")

    def after_visualizers_update(self):
        raise NotImplementedError("after_visualizers_update has not been implemented.")


class PyplotOutput(Output, CodeVisualizer):
    """VBox"""

    def __init__(self, figure):
        self.figure = figure

        super().__init__()

        self.figure.canvas.toolbar_visible = True
        self.figure.canvas.header_visible = False
        self.figure.canvas.footer_visible = False
        with self:
            # self.figure.canvas.show() does not work, dont understand
            # self.figure.show()
            plt.show(self.figure.canvas)

    def before_visualizers_update(self):
        for ax in self.figure.get_axes():
            if ax.has_data() or len(ax.artists) > 0:
                ax.clear()

    def after_visualizers_update(self):
        pass


class AnimationOutput(Output, CodeVisualizer):
    def __init__(self, figure, verbose=True):
        super().__init__()
        self.figure = figure
        self.animation = None
        self.verbose = verbose

    @property
    def figure(self):
        return self._figure

    @figure.setter
    def figure(self, new_figure):
        new_figure.canvas.toolbar_visible = True
        new_figure.canvas.header_visible = False
        new_figure.canvas.footer_visible = False
        plt.close(new_figure)
        self._figure = new_figure

    def before_visualizers_update(self):
        self.clear_output()
        for ax in self.figure.get_axes():
            if ax.has_data() or len(ax.artists) > 0:
                ax.clear()

    def after_visualizers_update(self):
        if self.animation is None:
            return
        with self:
            if self.verbose:
                print("Displaying animation...")
            display(IPython.display.HTML(self.animation.to_jshtml()), display_id=True)


class ClearedOutput(Output, CodeVisualizer):
    """Mini-wrapper for Output to provide an output space that gets cleared when it is updated e.g. to print some output or reload a widget."""

    def __init__(self):
        super().__init__()

    def before_visualizers_update(self):
        self.clear_output()

    def after_visualizers_update(self):
        pass
