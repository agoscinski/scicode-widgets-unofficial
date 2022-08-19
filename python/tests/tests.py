from ast import Assert
from configparser import MissingSectionHeaderError
import unittest
import sys
import os
import json

from IPython.display import display
from IPython.core.interactiveshell import InteractiveShell

from widget_code_input import WidgetCodeInput
import widget_code_input.utils as utils
from scwidgets import (CodeDemo, CodeChecker, ParametersBox, PyplotOutput, ClearedOutput, TextareaAnswer, AnswerRegistry)

import matplotlib.pyplot as plt
import matplotlib

from parameterized import parameterized_class
# same backend as in jupyter notebook
matplotlib.use('module://ipympl.backend_nbagg')


class SupressStdOutput():
    def __init__(self, redirect_to_null=False, suppress_error=False):
        self.suppress_error = suppress_error
        self.redirect_to_null = redirect_to_null
        self._file = None

    def __enter__(self):
        self.stdout = sys.stdout
        if self.redirect_to_null:
            self._file = open('/dev/null', 'w')
            sys.stdout = self._file
        else:
            sys.stdout = None

    def __exit__(self, etype, evalue, tb):
        sys.stdout = self.stdout
        if self.redirect_to_null:
            self._file.close()
        if etype is None or self.suppress_error:
            return True
        return False

    def clear_output(self):
        pass

# a bunch of test TODO needs organization
class TestMain(unittest.TestCase):
    def setUp(self):
        self.working_code_input = WidgetCodeInput(
                function_name="test",
                function_parameters="a",
                docstring="",
                function_body="return a+1")
        self.failing_name_error_code_input = WidgetCodeInput(
                function_name="test",
                function_parameters="a",
                docstring="",
                function_body="return b")
        self.failing_syntax_error_code_input = WidgetCodeInput(
                function_name="test",
                function_parameters="a",
                docstring="",
                function_body="5a")
        self.test_code_checker = CodeChecker({(1,):(2,), (2,):(3,)})

        self.parbox = ParametersBox(a = (1., -4, 4, 1, 'a'))

        self.test_code_demo = CodeDemo(code_input=self.working_code_input,
                    input_parameters_box=self.parbox,
                    visualizers=[ClearedOutput()],
                    update_on_input_parameter_change=False,
                    update_visualizers=lambda a, wci, visualizer: a,
                    code_checker=self.test_code_checker,
                    separate_check_and_update_buttons=True)

        InteractiveShell.instance()

    def test_nb_checks(self):
        # tests if the code_checker is initialized with the correct number of checks
        assert self.test_code_checker.nb_checks == 2

    def test_code_checker_check(self):
        # tests if the checking a failing WidgetCodeInput outputs the correct exception 
        self.test_code_checker.check(self.working_code_input)
        self.assertRaises((NameError, utils.CodeValidationError), self.test_code_checker.check, self.failing_name_error_code_input)

    def test_code_demo_callback_on_display(self):
        # tests if on_displayed callback works properly

        update_was_run = False
        def update_function(a, code_input, visualizer):
            nonlocal update_was_run
            update_was_run = True

        self.test_code_demo.update_visualizers = update_function
        # display does not work for None stdout so we direct to null
        with SupressStdOutput(redirect_to_null=True):
            display(self.test_code_demo)
        self.assertTrue(update_was_run)

    def test_code_demo_check(self):
        # tests if .check() works properly
        self.test_code_demo.check()

    def test_code_demo_check_click(self):
        # tests if check_button.click works properly
        self.test_code_demo.check_button.click()

    @unittest.expectedFailure 
    def test_code_demo_without_update_button(self):
        #Checks if an error is raised when CodeDemo without update buttons are updated 
        code_demo = CodeDemo(
                    input_parameters_box=self.parbox,
                    visualizers=[ClearedOutput()],
                    update_visualizers= lambda a, visualizer: a)
        self.assertFalse(code_demo.has_update_button())
        self.assertRaises(Exception,code_demo.update)
    @unittest.expectedFailure 
    def test_code_demo_without_check_button(self):
        #Checks if an error is raised when CodeDemos without check button are checked 
        code_demo = CodeDemo(
                    input_parameters_box=self.parbox,
                    visualizers=[ClearedOutput()],
                    update_visualizers= lambda a, visualizer: a)
        self.assertFalse(code_demo.has_check_button())
        self.assertRaises(Exception,code_demo.check)

    #def test_pyplot_output(self):
    #    # TODO(alex) gives a lot of deprecation warnings fix this before uncommenting test
    #    test_fig = plt.figure()
    #    PyplotOutput(test_fig)

    def test_code_demo_check_after_erroneous_check(self):
        # Checks if the check button gets enabled again after a check has failed 
        # to verify that we actually have run the check function within the code demo
        failing_check_has_run = False
        def failing_check_function(a,b):
            nonlocal failing_check_has_run
            failing_check_has_run = True
            raise NameError
            return False
        self.test_code_demo.code_checker.equality_function = failing_check_function
        self.test_code_demo._error_output = SupressStdOutput(suppress_error=True)
        self.test_code_demo.check_button.click()
        self.assertTrue(failing_check_has_run)
        # check if button_enabled
        self.assertFalse(self.test_code_demo.check_button.disabled, "check button is disabled but it should be enabled")
        # check if validation text value is correct
        nb_failed_checks = self.test_code_checker.nb_checks
        ref_validation_text_value = "&nbsp;" * 4 +  f"   {nb_failed_checks} out of {self.test_code_checker.nb_checks} tests failed."
        self.assertEqual(self.test_code_demo._validation_text.value, ref_validation_text_value)

    def test_code_demo_update_button_enabled_after_erroneous_update(self):
        # Checks if the update button gets enabled again after an update has failed 
        # to verify that we actually have run the update function within the code demo
        update_was_run = False
        def erroneous_update_function(a, wci, visualizers):
            nonlocal update_was_run
            update_was_run = True
            raise NameError
        # TODO setter does not work why?
        self.test_code_demo.update_visualizers = erroneous_update_function
        self.test_code_demo._error_output = SupressStdOutput(suppress_error=True)
        self.test_code_demo.update_button.click()
        self.assertTrue(update_was_run)
        self.assertFalse(self.test_code_demo.update_button.disabled)

@parameterized_class(("name","answer"), [
   ("TextareaAnswer",TextareaAnswer(), ),
   ("CodeDemo",CodeDemo(
            code_input=  WidgetCodeInput(
                function_name="name", 
                function_parameters="",
                docstring="""""",
                function_body="""body"""),
            input_parameters_box=None,
            visualizers=None,
            update_visualizers=None,
            code_checker=None,
            separate_check_and_update_buttons=False,
            update_on_input_parameter_change=False
), )
])
class TestAnswerRegistry(unittest.TestCase):
    def setUp(self):
        self.answer_registry = AnswerRegistry(prefix="test")
        self.answer_registry._author_name_text.value = "MaxMustermann"
        self.answer_registry.register_answer_widget("textarea_key", self.answer)
        self.answer_registry._output = SupressStdOutput()
        InteractiveShell.instance()

    def tearDown(self):
        if os.path.exists("test-MaxMustermann.json"):
            os.remove("test-MaxMustermann.json")

    def test_update_save_widgets(self):
        # checks if a new callback has been created but widget stays the same
        old_callback = self.answer_registry._callbacks["textarea_key"]
        self.assertTrue(self.answer_registry._answer_widgets["textarea_key"] == self.answer)

        self.answer_registry.register_answer_widget("textarea_key", self.answer)

        self.assertTrue(self.answer_registry._answer_widgets["textarea_key"] == self.answer)
        self.assertTrue(self.answer_registry._callbacks["textarea_key"] != old_callback)

    def test_load_answers(self):
        # Creates a new file with AnswerRegistry using the load_button and checks if file has been created
        self.answer_registry._load_answers_button.click()
        self.assertTrue(os.path.exists("test-MaxMustermann.json"))

    def test_answer_correctly_saved(self):
        # Checks if a saved answer and it's value are correctly saved in the Answer .json file
        self.answer.answer_value = "saved_answer"
        self.answer_registry._load_answers_button.click() 
        self.answer._save_button.click()
        # the answer_value should be now stored in the json answers file
        with open("test-MaxMustermann.json", "r") as answers_file:
            saved_answers_file = json.load(answers_file)
            self.assertTrue("textarea_key" in saved_answers_file)
            self.assertEqual(saved_answers_file["textarea_key"],"saved_answer")

    def test_raise_error(self):
        # Checks if errors are correctly shown as Outputs in the notebook.
        assertTrue = self.assertTrue
        class AssertRaiseOutput(SupressStdOutput):
            def __exit__(self, etype, evalue, tb):
                super().__exit__(etype, evalue, tb)
                nonlocal assertTrue
                test_condition = etype is FileNotFoundError
                assertTrue(test_condition) 
                return True
        self.answer._save_output = AssertRaiseOutput()
        self.answer._save_button.click() 