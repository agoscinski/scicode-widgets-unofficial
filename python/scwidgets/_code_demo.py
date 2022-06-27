from abc import abstractmethod
import warnings

import sys
import traitlets
import matplotlib.pyplot as plt
import numpy as np

from collections.abc import Iterable
from ipywidgets import (
    Output,
    FloatSlider,
    IntSlider,
    Box,
    HBox,
    VBox,
    Layout,
    Checkbox,
    Dropdown,
    Button,
    HTML,
    Text,
    Label,
)
import IPython.display
import inspect

# TODO save function

# TODO(low) need to consider traits
def copy_widget(widget):
    signature = inspect.getfullargspec(type(widget).__init__)
    return type(widget)(*[getattr(widget, arg) for arg in signature.args[1:]])


# TODO(low) checkbox
class ParametersBox(VBox):
    value = traitlets.Dict({}, sync=True)

    def __init__(self, **kwargs):
        # TODO(low) continuous_update does not work atm, check later after the rest has been fixed
        self._controls = {}
        for k, v in kwargs.items():
            if type(v) is tuple:
                if type(v[0]) is float:
                    (
                        val,
                        min,
                        max,
                        step,
                        desc,
                        slargs,
                    ) = ParametersBox.float_make_canonical(k, *v)
                    self._controls[k] = FloatSlider(
                        value=val,
                        min=min,
                        max=max,
                        step=step,
                        description=desc,
                        continuous_update=False,
                        style={"description_width": "initial"},
                        layout=Layout(width="50%", min_width="5in"),
                        **slargs,
                    )
                elif type(v[0]) is int:
                    (
                        val,
                        min,
                        max,
                        step,
                        desc,
                        slargs,
                    ) = ParametersBox.int_make_canonical(k, *v)
                    self._controls[k] = IntSlider(
                        value=val,
                        min=min,
                        max=max,
                        step=step,
                        description=desc,
                        continuous_update=False,
                        style={"description_width": "initial"},
                        layout=Layout(width="50%", min_width="5in"),
                        **slargs,
                    )
                elif type(v[0]) is bool:
                    val, desc, slargs = ParametersBox.bool_make_canonical(k, *v)
                    self._controls[k] = Checkbox(
                        value=val,
                        description=desc,
                        continuous_update=False,
                        style={"description_width": "initial"},
                        layout=Layout(width="50%", min_width="5in"),
                        **slargs,
                    )
                elif type(v[0]) is str:
                    val, desc, options, slargs = ParametersBox.str_make_canonical(k, *v)
                    self._controls[k] = Dropdown(
                        options=options,
                        value=val,
                        description=desc,
                        disabled=False,
                        style={"description_width": "initial"},
                        layout=Layout(width="50%", min_width="5in"),
                    )
                else:
                    raise ValueError("Unsupported parameter type")
            else:
                # assumes an explicit control has been passed
                self._controls[k] = v

        super().__init__()
        self.children = [control for control in self._controls.values()]

        # links changes to the controls to the value dict
        for k in self._controls:
            self._controls[k].observe(self._parameter_handler(k), "value")
            self.value[k] = self._controls[k].value

    def _parameter_handler(self, k):
        def _update_parameter(change):
            # traitlets.Dict cannot track updates, only assignment
            dict_copy = self.value.copy()
            dict_copy[k] = self._controls[k].value
            self.value = dict_copy

        return _update_parameter

    @property
    def parameters(self):
        return tuple(self.value.values())

    @staticmethod
    def float_make_canonical(
        key, default, minval=None, maxval=None, step=None, desc=None, slargs=None, *args
    ):
        # gets the (possibly incomplete) options for a float value, and completes as needed
        if minval is None:
            minval = min(default, 0)
        if maxval is None:
            maxval = max(default, 100)
        if step is None:
            step = (maxval - minval) / 100
        if desc is None:
            desc = key
        if slargs is None:
            slargs = {}
        if len(args) > 0:
            raise ValueError("Too many options for a float parameter")
        return default, minval, maxval, step, desc, slargs

    @staticmethod
    def int_make_canonical(
        key, default, minval=None, maxval=None, step=None, desc=None, slargs=None, *args
    ):
        # gets the (possibly incomplete) options for a int value, and completes as needed
        if minval is None:
            minval = min(default, 0)
        if maxval is None:
            maxval = max(default, 10)
        if step is None:
            step = 1
        if desc is None:
            desc = key
        if slargs is None:
            slargs = {}
        if len(args) > 0:
            raise ValueError("Too many options for a int parameter")
        if type(minval) is not int or type(maxval) is not int or type(step) is not int:
            raise ValueError("Float option for an int parameter")
        return default, minval, maxval, step, desc, slargs

    @staticmethod
    def bool_make_canonical(key, default, desc=None, slargs=None, *args):
        # gets the (possibly incomplete) options for a bool value, and completes as needed
        if desc is None:
            desc = key
        if slargs is None:
            slargs = {}
        if len(args) > 0:
            raise ValueError("Too many options for a bool parameter")
        return default, desc, slargs

    @staticmethod
    def str_make_canonical(key, default, options, desc=None, slargs=None):
        if desc is None:
            desc = key
        if slargs is None:
            slargs = {}
        if not (all([type(option) is str for option in options])):
            raise ValueError("Non-str in options")
        return default, desc, options, slargs


class CodeChecker:
    """
    reference_code_parameters : dict
    """

    def __init__(self, reference_code_parameters, equality_function=None):
        self.reference_code_parameters = reference_code_parameters

        self.equality_function = equality_function
        if self.equality_function is None:
            self.equality_function = np.allclose

    @property
    def nb_checks(self):
        return (
            0
            if self.reference_code_parameters is None
            else len(self.reference_code_parameters)
        )

    def check(self, code_input):
        def student_code_wrapper(*args, **kwargs):
            # For checking we ignore
            try:
                orig_stdout = sys.stdout
                out = code_input.get_function_object()(*args, **kwargs)
                sys.stdout = orig_stdout
            except Exception as e:
                sys.stdout = orig_stdout
                # because some errors in code widgets do not print the
                # traceback correctly, we print the last step manually
                tb = sys.exc_info()[2]
                while not (tb.tb_next is None):
                    tb = tb.tb_next
                if tb.tb_frame.f_code.co_name == code_input.function_name:
                    # index = line-1
                    line_number = tb.tb_lineno - 1
                    code = (
                        code_input.function_name
                        + '"""\n'
                        + code_input.docstring
                        + '"""\n'
                        + code_input.function_body
                    ).splitlines()
                    error = f"<widget_code_input.widget_code_input in {code_input.function_name}({code_input.function_parameters})\n"
                    for i in range(
                        max(0, line_number - 2), min(len(code), line_number + 3)
                    ):
                        if i == line_number:
                            error += f"----> {i} {code[i]}\n"
                        else:
                            error += f"      {i} {code[i]}\n"
                    e.args = (str(e.args[0]) + "\n\n" + error,)
                raise e
            return out

        if isinstance(self.reference_code_parameters, dict):
            iterator = self.reference_code_parameters.items()
        # TODO not clear what it is in case not a dict
        else:
            iterator = self.reference_code_parameters

        nb_failed_checks = 0
        for x, y in iterator:
            out = student_code_wrapper(*x)
            nb_failed_checks += int(not (self.equality_function(y, out)))
        return nb_failed_checks


class CodeDemo(VBox):
    """
    Widget to demonstrate code interactively in a variety of ways.

    A code demo is in essence a combination of the widgets: one `code_input` + one `input_parameters_box` + one or more `code_visualizer`. Any widget can also be set None and is then not displayed.


    Parameters
    ----------
        code_input : WidgetCodeInput, default=None
            An widget supporting the input of code usually for a student to fill in a solution.
        input_parameters_box : ParametersBox, default=None
        update_on_input_parameter_change : bool, default=True
            Determines if the visualizers are instantly updated on a parameter change of `input_parameters_box`. If processing the code is computationally demanding, this parameter should be set to False for a better user experience. The user then has to manually update by a button click.
        update_visualizers : function, default=None
            It processes the code `code_input` and to updae the `visualizers`. The `update_visualizers` function is assumed to support the signature
            def update_visualizers(*input_parameters_box.paramaters, code_input if not None, visualizers if not None)
        visualizers : displayable Widget, default=None
            Any kind of widget that can be displayed. Optionally the visualizer has a `before_visualizers_update` and/or a `after_visualizers_update` function which allows set up the visualizer before and after the `update_visualizers` function is executed
        code_checker : CodeChecker
            It handles the correctness check of the code in `code_input`.
        separate_check_and_update_buttons: bool, default=False
            It handles the correctness check of the code in `code_input`.

    """

    def __init__(
        self,
        code_input=None,
        input_parameters_box=None,
        update_on_input_parameter_change=True,
        visualizers=None,
        update_visualizers=None,
        code_checker=None,
        separate_check_and_update_buttons=False,
    ):

        self._code_input = code_input
        self._input_parameters_box = input_parameters_box

        if visualizers is not None:
            if not (isinstance(visualizers, Iterable)):
                self._visualizers = [visualizers]
            else:
                self._visualizers = visualizers
        else:
            self._visualizers = []

        self._update_on_input_parameter_change = update_on_input_parameter_change
        self._update_visualizers = update_visualizers
        self._code_checker = code_checker
        self._separate_check_and_update_buttons = separate_check_and_update_buttons

        if (
            self._input_parameters_box is None
            and self._update_on_input_parameter_change
        ):
            warnings.warn(
                "`update_on_input_parameter_change` is True, but `input_parameters_box` is None. `update_on_input_parameter_change` does not affect anything without a `input_parameters_box`"
            )
        # TODO should this be mentioned to the user?
        # if len(self._visualizers) == 0 and self._update_visualizers is not None:
        #    warnings.warn("self._update_visualizers is given without visualizers.")
        if len(self._visualizers) > 0 and self._update_visualizers is None:
            raise ValueError(
                "Non-empty not None `visualizers` are given but without a `update_visualizers` function. The `visualizers` are used by the code demo"
            )

        if self._update_on_input_parameter_change:
            self._input_parameters_box.observe(self.update, "value")

        self._error_output = Output(layout=Layout(width="100%", height="100%"))

        if self.has_check_button() and self.has_update_button():
            if self._separate_check_and_update_buttons:
                check_button = Button(description="Check")
                check_button.on_click(self.check)
                update_button = Button(description="Update")
                update_button.on_click(self.update)
                self._demo_button_box = HBox([check_button, update_button])
            else:
                check_and_update_button = Button(description="Check & update")
                check_and_update_button.on_click(self.check_and_update)
                self._demo_button_box = HBox([check_and_update_button])
        elif not (self.has_check_button()) and self.has_update_button():
            update_button = Button(description="Update")
            update_button.on_click(self.update)
            self._demo_button_box = HBox([update_button])
        elif self.has_check_button() and not (self.has_update_button()):
            check_button = Button(description="Check")
            check_button.on_click(self.check)
            self._demo_button_box = HBox([check_button])
        else:
            self._demo_button_box = None

        self._validation_text = HTML(value="")

        self._error_output = Output(layout=Layout(width="100%", height="100%"))

        demo_widgets = []
        if self._code_input is not None:
            demo_widgets.append(self._code_input)

        if self.has_check_button():
            demo_widgets.append(
                HBox(
                    [self._demo_button_box, self._validation_text],
                    layout=Layout(align_items="center"),
                )
            )
            demo_widgets.append(self._error_output)
        elif not (self.has_check_button()) and self.has_update_button():
            demo_widgets.append(self._demo_button_box)

        if input_parameters_box is not None:
            demo_widgets.append(self._input_parameters_box)

        demo_widgets.extend(self._visualizers)

        super().__init__(demo_widgets)

        # needed for chemiscope, chemiscope does not acknowledge updates of settings
        # until the widget has been displayed
        # TODO why this function does not work "self.on_displayed(self, self.update)"  but this one?
        self._display_callbacks.register_callback(self.update)

    def has_update_button(self):
        # to cover the cases where no code input is used
        without_code_input_demo = (
            (len(self._visualizers) > 0)
            and (not (self._update_on_input_parameter_change))
            and (self._input_parameters_box is not None)
        )
        with_code_input_demo = (
            len(self._visualizers) > 0 and self._code_input is not None
        )
        return without_code_input_demo or with_code_input_demo

    def has_check_button(self):
        return (self._code_checker is not None) and (self._code_checker.nb_checks > 0)

    def check_and_update(self, change=None):
        self.check(change)
        self.update(change)

    def check(self, change=None):
        if self.has_check_button():
            self.check_button.disabled = True
        if self._code_checker is None:
            return 0
        self._error_output.clear_output()
        nb_failed_checks = 0
        with self._error_output:
            nb_failed_checks = self._code_checker.check(self._code_input)

        self._validation_text.value = "&nbsp;" * 4
        if nb_failed_checks:
            self._validation_text.value += f"   {nb_failed_checks} out of {self._code_checker.nb_checks} tests failed."
        else:
            self._validation_text.value += (
                f"<span style='color:green'> All tests passed!</style>"
            )
        if self.has_check_button():
            self.check_button.disabled = False
        return nb_failed_checks

    @property
    def update_button(self):
        if self.has_update_button():
            if len(self._demo_button_box.children) > 1:
                return self._demo_button_box.children[1]
            else:
                return self._demo_button_box.children[0]
        else:
            return None

    @property
    def check_button(self):
        if self.has_check_button():
            return self._demo_button_box.children[0]
        else:
            return None

    def update(self, change=None):
        if self.has_update_button():
            self.update_button.disabled = True

        if self._visualizers is not None:
            for visualizer in self._visualizers:
                if hasattr(visualizer, "before_visualizers_update"):
                    visualizer.before_visualizers_update()

        if self._update_visualizers is not None:
            if self._input_parameters_box is None:
                parameters = []
            else:
                parameters = self._input_parameters_box.parameters

            if self._code_input is not None and self._visualizers is not None:
                self._update_visualizers(
                    *parameters, self._code_input, self._visualizers
                )
            elif self._code_input is not None and self._visualizers is None:
                self._update_visualizers(*parameters, self._code_input)
            elif self._code_input is None and self._visualizers is not None:
                self._update_visualizers(*parameters, self._visualizers)
            else:
                self._update_visualizers(*parameters)

        if self._visualizers is not None:
            for visualizer_output in self._visualizers:
                if hasattr(visualizer, "after_visualizers_update"):
                    visualizer.after_visualizers_update()

        if self.has_update_button():
            self.update_button.disabled = False

    @property
    def code_input(self):
        return self._code_input

    @property
    def input_parameters_box(self):
        return self._input_parameters_box

    @property
    def update_on_input_parameter_change(self):
        return self._update_on_input_parameter_change

    @property
    def visualizers(self):
        return self._visualizers

    @property
    def update_visualizers(self):
        return self._update_visualizers

    @property
    def code_checker(self):
        return self._code_checker

    @property
    def separate_check_and_update_buttons(self):
        return self._separate_check_and_update_buttons


class CodeVisualizer:
    """CodeDemo supports this interface to execute code before and after the update of the visualizers. It does not inherit from ABC, because then it would conflict with the inheritence of widgets."""

    @abstractmethod
    def before_visualizers_update(self):
        raise NotImplementedError("before_visualizers_update has not been implemented.")

    @abstractmethod
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
