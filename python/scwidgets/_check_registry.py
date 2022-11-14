"""
# checker function must be named arguments
def code_input(*, a=5, b=1):
    return
input_parameters = [{'a': 1, 'b':2}] : list of dicts, each dict one corresponds to one check with current configuration, arguments are only kwargs
args is reserved for
output_parameters = [output_for_input1, output_for_input2]
fingerprint(output1):
    return output1

fingerprint has to transform the output into a form that the equal function can interpret
it also can to type checks

renaming
fingerprint -> process_output

function flow:
    output = widget.run_code(input)
    output = process_output(output) -> can raise assertion errors [if not None]
    if process_output is None:
        type check for output
        len/shape check for output
    custom_assert(output, reference_output) -> can raise assertion errors     [if not None]
    equal(output, reference_output) -> can raise assertion errors  [if not None]

function flow if processed_output is None:
    output = widget.run_code(input)
    custom_assert(processed_output, reference_output) -> can raise assertion errors   [if not None]
    equal(processed_output, reference_output) -> can raise assertion errors    [if not None]
"""

class CodeCheckerRegistry:
    """
    execercise_id : Widget or str
        is an identifier for an execrcise. it can be a name or a widget
    """
    def __init__(self):
        self._exercises = {}
        self._widgets = {}

    @property
    def exercises(self):
        return self._exercises

    def init_checks(self, exercise_name, widget):
        """initialize checks, if checks exist then it resets them"""
        self._exercises[exercise_name] = []
        self._widgets[exercise_name] = widget

    def add_check(self, exercise_name, inputs_parameters, reference_output=None, process_output=None, custom_assert=None, equal=None):
        check = Check(self._widgets[exercise_name], inputs_parameters, reference_output, process_output, custom_assert, equal)
        self._exercises[exercise_name].append(check)

    def produce_reference_outputs(self, exercise_name, change=None):
        for check in self._exercises[exercise_name]:
            check.produce_reference_outputs()

    def run_checks(self, exercise_name, change=None):
        for check in self._exercises[exercise_name]:
            success = check.run_check()
        return success

    def dump_exercise_checks_to_pickle(self, filename):
        pickle.dump(self.exercises, filename)

    def loads_checks_from_pickle(self, filename):
        self.exercises = pickle.load(filename)


# name check -> checker?? 
class Check:
    """
    inputs_parameters: list of inputs
    reference_outputs: list of reference outputs
    process_output : function
    custom_assert : function
    equal : function
    """
    def __init__(self, widget, inputs_parameters, reference_output=None, process_output=None, custom_assert=None, equal=None):
        if not(hasattr(widget, "check_output")):
            raise ValueError("Widget does not have output with name 'check_output', which is needed to forward output to widget.")
        if not(hasattr(widget, "produce_output")):
            raise ValueError("Widget does not have function with name 'produce_output', which is needed to produce refeference outputs.")

        if reference_output is not None and len(reference_outputs) != len(inputs_parameters):
            raise ValueError(f"Number of inputs and outputs must be the same: len(inputs_parameters) != len(reference_outputs) ({len(inputs_parameters)} != {len(reference_outputs)})")

        self._widget = widget
        self._inputs_parameters = inputs_parameters
        self._reference_output = reference_output
        self._process_output = process_output
        self._custom_assert = custom_assert
        self._equal = equal

    def produce_reference_outputs(self):
        self._reference_outputs = []
        for input_parameters in self._inputs_parameters:
            try:
                reference_output = self._widget.produce_output(**input_parameters)
            except Exception as e:
                with self._widget.check_output:
                    raise e
                return False
            self._reference_outputs.append(reference_output)

    def run_check(self):
        if self._reference_outputs is None:
            raise ValueError("Reference outputs are None. Please first run produce_reference_outputs or specify reference_outputs on initialization.")
        for i in range(len(self._reference_outputs)):
            with self._widget.check_output:
                output = self._widget.produce_output(**self._inputs_parameters[i])
                output = output if (self._process_output is None) \
                            else self._process_output(output)
            if self._process_output is None:
                if not(isinstance)(output, type(self._reference_outputs[i])):
                    with self._widget.check_output:
                        print(f"TypeCheck failed: Expected type {type(self._reference_outputs[i])} but got {type(output)}.")
                    return False
                elif hasattr(self._reference_outputs[i], "shape") and (output.shape != self._reference_outputs[i].shape):
                    with self.widget.check_output:
                        print(f"ShapeCheck failed: Expected shape {self._reference_outputs[i].shape} but got {output.shape}.")
                    return False
                elif hasattr(self._reference_outputs[i], "__len__") and (len(output) != len(self._reference_outputs[i])):
                    with self.widget.check_output:
                        print(f"CheckAssert failed: Expected len {self._reference_outputs[i]} but got {len(output)}.")
                    return False
            if self._custom_assert is not None:
                try:
                    self.custom_assert(out_student, out_teacher)
                except AssertionError as e:
                    with self._widget.check_output:
                        print(f"CustomCheck failed: {e}")
                    checks_successful = False
            if (self._equal is not None) and not(self._equal(output, self._reference_outputs[i])):
                print(f"EqualCheck failed: Expected {self._reference_outputs[i]} but got {output}.")
                return False
            return True
