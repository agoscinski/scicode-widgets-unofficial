from abc import abstractmethod

import sys
import traitlets
import matplotlib.pyplot as plt
import numpy as np

from collections.abc import Iterable
from ipywidgets import (Output, FloatSlider, IntSlider,
                        Box, HBox, VBox, Layout, Checkbox, Dropdown,
                        Button, HTML, Text, Label)
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
                    val, min, max, step, desc, slargs = ParametersBox.float_make_canonical(k, *v)
                    self._controls[k] = FloatSlider( value=val, min=min, max=max, step=step,
                                                    description=desc, continuous_update=False,
                                                    style={'description_width': 'initial'}, 
                                                    layout=Layout(width='50%', min_width='5in'),
                                                    **slargs)   
                elif type(v[0]) is int:
                    val, min, max, step, desc, slargs = ParametersBox.int_make_canonical(k, *v)                    
                    self._controls[k] = IntSlider( value=val, min=min, max=max, step=step,
                                                    description=desc, continuous_update=False,
                                                    style={'description_width': 'initial'}, 
                                                    layout=Layout(width='50%', min_width='5in'),
                                                    **slargs)   
                elif type(v[0]) is bool:
                    val, desc, slargs = ParametersBox.bool_make_canonical(k, *v)
                    self._controls[k] = Checkbox(value = val, description=desc, continuous_update=False, 
                                                  style={'description_width': 'initial'}, 
                                                  layout=Layout(width='50%', min_width='5in'),
                                                  **slargs
                                                )
                elif type(v[0]) is str:
                    val, desc, options, slargs = ParametersBox.str_make_canonical(k, *v)
                    self._controls[k] = Dropdown(
                        options=options,
                        value=val,
                        description=desc,
                        disabled=False,
                        style={'description_width': 'initial'}, 
                        layout=Layout(width='50%', min_width='5in')
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
            self._controls[k].observe(self._parameter_handler(k), 'value')
            self.value[k] = self._controls[k].value

    def _parameter_handler(self, k):
        def _update_parameter(change):
            # traitlets.Dict cannot track updates, only assignment
            dict_copy = self.value.copy()
            dict_copy[k] = self._controls[k].value
            self.value = dict_copy
        return _update_parameter

    # TODO make property
    def get_parameters(self):
        return tuple(self.value.values())

    @staticmethod
    def float_make_canonical(key, default, minval=None, maxval=None, step=None, desc=None, slargs=None, *args):
        # gets the (possibly incomplete) options for a float value, and completes as needed
        if minval is None:
            minval = min(default, 0)
        if maxval is None:
            maxval = max(default, 100)
        if step is None:
            step = (maxval-minval)/100
        if desc is None:
            desc = key
        if slargs is None:
            slargs = {}
        if len(args)>0:
            raise ValueError("Too many options for a float parameter")
        return default, minval, maxval, step, desc, slargs

    @staticmethod
    def int_make_canonical(key, default, minval=None, maxval=None, step=None, desc=None, slargs=None, *args):
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
        if len(args)>0:
            raise ValueError("Too many options for a int parameter")
        if type(minval) is not int or  type(maxval) is not int or type(step) is not int:
            raise ValueError("Float option for an int parameter")
        return default, minval, maxval, step, desc, slargs

    @staticmethod
    def bool_make_canonical(key, default, desc=None, slargs=None, *args):
        # gets the (possibly incomplete) options for a bool value, and completes as needed
        if desc is None:
            desc = key
        if slargs is None:
            slargs = {}
        if len(args)>0:
            raise ValueError("Too many options for a bool parameter")
        return default, desc, slargs

    @staticmethod
    def str_make_canonical(key, default, options, desc=None, slargs=None):
        if desc is None:
            desc = key
        if slargs is None:
            slargs = {}
        if not(all([type(option) is str for option in options])):
            raise ValueError("Non-str in options")
        return default, desc, options, slargs

class CodeChecker():
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
        return 0 if self.reference_code_parameters is None else len(self.reference_code_parameters)

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
                while not(tb.tb_next is None):
                    tb = tb.tb_next
                if (tb.tb_frame.f_code.co_name == code_input.function_name):
                    # index = line-1
                    line_number = tb.tb_lineno-1
                    code = (code_input.function_name +
                            '"""\n' + code_input.docstring + '"""\n' +
                            code_input.function_body).splitlines()
                    error = f"<widget_code_input.widget_code_input in {code_input.function_name}({code_input.function_parameters})\n"
                    for i in range(max(0, line_number-2), min(len(code), line_number+3)):
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
            nb_failed_checks += int(not(self.equality_function(y, out)))
        return nb_failed_checks

class CodeDemo(VBox):
    """
    Parameters
    ----------
        code_input : WidgetCodetInput
        input_parameters_box : ParametersBox
        process_code : function
            processes the function of `code_input` to create visualization using code_visualizers
            Should have the same args as the `input_parameters_box.paramater)` and should then the args `code_input_function` and `code_visualizers` if not None
        code_input_checker : CodeChecker
        update_on_input_parameter_change : bool 
            Deterimines if the visualizers are instantaneously updated on a parameter change of `input_parameters_box`

    """
    # TODO rename code_visualizers to code_visualizer, it can be other widgets (chemiscope)
    def __init__(self,
            code_input=None,
            input_parameters_box=None,
            code_visualizers=None,
            update_on_input_parameter_change=True,
            process_code=None,
            code_checker=None,
            separate_check_and_update_buttons=False):

        #TODO update_on_input_parameter_change -> instanteneous_update
        if input_parameters_box is None and update_on_input_parameter_change:
            # TODO make to warning
            raise ValueError("update_on_input_parameter_change does not work without parameter box")

        self.code_input = code_input
        self.input_parameters_box = input_parameters_box

        if code_visualizers is not None:
            if not(isinstance(code_visualizers, Iterable)):
                self.code_visualizers = [code_visualizers]
            else:
                self.code_visualizers = code_visualizers
        else:
            self.code_visualizers = []

        self.update_on_input_parameter_change = update_on_input_parameter_change
        self.process_code = process_code
        self.code_checker = code_checker
        self.separate_check_and_update_buttons = separate_check_and_update_buttons

        if len(self.code_visualizers) == 0 and self.process_code is not None:
            # TODO make to warning! Could be that global visualizer is used 
            # for some hacky solution
            raise ValueError("Cannot use self.process_code without visualizer outputs")
        if len(self.code_visualizers) > 0 and self.process_code is None:
            # TODO make to warning?
            raise ValueError("Cannot use visualizer outputs without process_code function")

        # TODO _demo_button_box -> _demo_buttons
        if self.update_on_input_parameter_change:
            self.input_parameters_box.observe(self.update, 'value')

        self.error_output = Output(layout=Layout(width='100%', height='100%'))

        if self.has_check_button() and self.has_update_button():
            if self.separate_check_and_update_buttons:
                check_button = Button(description="Check")
                check_button.on_click(self.check)
                update_button = Button(description="Update")
                update_button.on_click(self.update)
                self._demo_button_box = HBox([check_button, update_button])
            else:
                check_and_update_button = Button(description="Check & update")
                check_and_update_button.on_click(self.check_and_update)
                self._demo_button_box = HBox([check_and_update_button ])
        elif not(self.has_check_button()) and self.has_update_button():
            update_button = Button(description="Update")
            update_button.on_click(self.update)
            self._demo_button_box = HBox([update_button])
        elif self.has_check_button() and not(self.has_update_button()):
            check_button = Button(description="Check")
            check_button.on_click(self.check)
            self._demo_button_box = HBox([check_button])
        else:
            self._demo_button_box = None

        self._validation_text = HTML(value="")

        self.error_output = Output(layout=Layout(width='100%', height='100%'))

        demo_widgets = []
        if self.code_input is not None:
            demo_widgets.append(self.code_input)

        if self.has_check_button():
            demo_widgets.append(HBox([
                self._demo_button_box, self._validation_text],
                layout=Layout(align_items='center')))
            demo_widgets.append(self.error_output)
        elif not(self.has_check_button()) and self.has_update_button():
            demo_widgets.append(self._demo_button_box)

        if input_parameters_box is not None:
            demo_widgets.append(self.input_parameters_box)

        demo_widgets.extend(self.code_visualizers)

        # TODO change to python3 style super().__init__(demo_widgets)
        super().__init__(demo_widgets)

        # needed for chemiscope, chemiscope does not acknowledge update to settings
        # until the widget has been displayed

        # TODO why this function does not work 
        #self.on_displayed(self, self.update)
        # but this one?
        self._display_callbacks.register_callback(self.update)

    def has_update_button(self):
        # to cover the cases where no code input is used
        without_code_input_demo = (len(self.code_visualizers) > 0) and (
                not(self.update_on_input_parameter_change)) and (
                self.input_parameters_box is not None)
        with_code_input_demo = len(self.code_visualizers) > 0 and self.code_input is not None
        return without_code_input_demo or with_code_input_demo

    def has_check_button(self):
        return (self.code_checker is not None) and (self.code_checker.nb_checks > 0)

    ## TODO needed? I dont think so, check with chemiscope widget
    #def _fire_children_displayed(self):
    #    super()._fire_children_displayed()
    #    self.update()

    def check_and_update(self, change=None):
        self.check(change)
        self.update(change)

    def check(self, change=None):
        if self.has_check_button():
            self.check_button.disabled = True
        if self.code_checker is None:
            return 0
        self.error_output.clear_output()
        nb_failed_checks = 0
        with self.error_output:
            nb_failed_checks = self.code_checker.check(self.code_input)

        self._validation_text.value = "&nbsp;"*4
        if nb_failed_checks:
            self._validation_text.value += f"   {nb_failed_checks} out of {self.code_checker.nb_checks} tests failed."
        else:
            self._validation_text.value += f"<span style='color:green'> All tests passed!</style>"
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

        if self.code_visualizers is not None:
            for visualizer in self.code_visualizers:
                if hasattr(visualizer, 'pre_process_code_update'):
                    visualizer.pre_process_code_update()

        if self.process_code is not None:
            if self.input_parameters_box is None:
                parameters = []
            else:
                # TODO get_parameters to attribute
                parameters = self.input_parameters_box.get_parameters()

            if self.code_input is not None and self.code_visualizers is not None:
                self.process_code(*parameters, self.code_input, self.code_visualizers)
            elif self.code_input is not None and self.code_visualizers is None:
                self.process_code(*parameters, self.code_input)
            elif self.code_input is None and self.code_visualizers is not None:
                self.process_code(*parameters, self.code_visualizers)
            else:
                self.process_code(*parameters)

        if self.code_visualizers is not None:
            for visualizer_output in self.code_visualizers:
                if hasattr(visualizer, 'post_process_code_update'):
                    visualizer.post_process_code_update()

        if self.has_update_button():
            self.update_button.disabled = False


# Cannot mix the meta class with inheritance of Output which inherits from different meta classes.
# Only using abstractmethod does not do anything, so I use the raise error solution.
# A metaclass would be more advantageous because the error occurs on object creation
class VisualizerOutput():

    @abstractmethod
    def pre_process_code_update(self):
        raise NotImplementedError("pre_process_code_update has not been implemented.")
    @abstractmethod
    def post_process_code_update(self):
        raise NotImplementedError("post_process_code_update has not been implemented.")

class PyplotOutput(Output, VisualizerOutput):
    """VBox
    """
    def __init__(self, figure):
        self.figure = figure

        super().__init__()

        self.figure.canvas.toolbar_visible = True
        self.figure.canvas.header_visible = False
        self.figure.canvas.footer_visible = False
        with self:
            # self.figure.canvas.show() does not work, dont understand
            #self.figure.show()
            plt.show(self.figure.canvas)

    def pre_process_code_update(self):
        for ax in self.figure.get_axes():
            if ax.has_data() or len(ax.artists)>0:
                ax.clear()
                
    def post_process_code_update(self):
        pass

class AnimationOutput(Output, VisualizerOutput):
    def __init__(self, figure, verbose=True):
        super().__init__()
        self.figure = figure    
        self.animation = None
        self.verbose = verbose

        self.figure.canvas.toolbar_visible = True
        self.figure.canvas.header_visible = False
        self.figure.canvas.footer_visible = False        
        plt.close(self.figure)
        
    def pre_process_code_update(self):
        self.clear_output()
        for ax in self.figure.get_axes():
            if ax.has_data() or len(ax.artists)>0:
                ax.clear()

    def post_process_code_update(self):
        if self.animation is None:
            return
        with self:
            if self.verbose:
                print("Displaying animation...")
            display(IPython.display.HTML(self.animation.to_jshtml()), display_id=True)

class ClearedOutput(Output, VisualizerOutput):
    """Mini-wrapper for Output to provide an output space that gets cleared when it is updated e.g. to print some output or reload a widget."""

    def __init__(self):
        super().__init__()

    def pre_process_code_update(self):
        self.clear_output()

    def post_process_code_update(self):
        pass
