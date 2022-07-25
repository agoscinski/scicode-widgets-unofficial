import unittest
import sys
import os
import json

from IPython.display import display
from IPython.core.interactiveshell import InteractiveShell

from widget_code_input import WidgetCodeInput
from scwidgets import (CodeDemo, CodeChecker, ParametersBox, PyplotOutput, ClearedOutput, TextareaAnswer, AnswerRegistry)

import matplotlib.pyplot as plt
import matplotlib
# same backend as in jupyter notebook
matplotlib.use('module://ipympl.backend_nbagg')



# TODO fix typo in class name
class SurpressStdOutput():
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
        assert self.test_code_checker.nb_checks == 2

    def test_code_checker_check(self):
        self.test_code_checker.check(self.working_code_input)
        self.assertRaises(NameError, self.test_code_checker.check, self.failing_name_error_code_input)

    def test_code_demo_callback_on_display(self):
        # tests if on_displayed callback works properly

        update_was_run = False
        def update_function(a, code_input, visualizer):
            nonlocal update_was_run
            update_was_run = True

        self.test_code_demo.update_visualizers = update_function
        # display does not work for None stdout so we direct to null
        with SurpressStdOutput(redirect_to_null=True):
            display(self.test_code_demo)
        self.assertTrue(update_was_run)

    def test_code_demo_check(self):
        self.test_code_demo.check()

    def test_code_demo_check_click(self):
        self.test_code_demo.check_button.click()


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
        self.test_code_demo._error_output = SurpressStdOutput(suppress_error=True)
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
        self.test_code_demo._error_output = SurpressStdOutput(suppress_error=True)
        self.test_code_demo.update_button.click()
        self.assertTrue(update_was_run)
        self.assertFalse(self.test_code_demo.update_button.disabled)

class TestAnswerRegistry(unittest.TestCase):
    def setUp(self):
        # @Joao setUp is invoked before each test, so you get clean objects for each test
        self.answer_registry = AnswerRegistry(prefix="test")
        self.textarea_answer = TextareaAnswer() 
        self.answer_registry._author_name_text.value = "Max Mustermann"
        self.answer_registry.register_answer_widget("textarea_key", self.textarea_answer)
        self.answer_registry._output = SurpressStdOutput()
        InteractiveShell.instance()

    def tearDown(self):
        # @Joao tearDown is invoked after each test, so you get clean every created file
        if os.path.exists("test-MaxMustermann.json"):
            os.remove("test-MaxMustermann.json")

    def test_update_save_widgets(self):
        # checks if a new callback has been created but widget stays the same
        old_callback = self.answer_registry._callbacks["textarea_key"]
        self.assertTrue(self.answer_registry._answer_widgets["textarea_key"] == self.textarea_answer)

        self.answer_registry.register_answer_widget("textarea_key", self.textarea_answer)

        self.assertTrue(self.answer_registry._answer_widgets["textarea_key"] == self.textarea_answer)
        self.assertTrue(self.answer_registry._callbacks["textarea_key"] != old_callback)


    def test_load_answers(self):
        # Creates a new file with AnswerRegistry using the load_button and checks if file has been created
        self.answer_registry._load_answers_button.click()
        self.assertTrue(os.path.exists("test-MaxMustermann.json"))

    def test_answer_correctly_saved(self):
        # TODO(Joao) so here something similar as in the above text, now set answer_value in the textarea to s.th. and check if it is stored in the json file after clicking on the save button
        #self.textarea_answer.answer_value = ... TODO
        self.answer_registry._load_answers_button.click() 
        self.textarea_answer._save_button.click()
        # the answer_value should be now stored in the json answers file
        # @Joao load the saved json file and check value of "textarea_key" 
        with open("test-MaxMustermann.json", "r") as answers_file:
            saved_answers_file = json.load(answers_file) # <--- this is a dict
            # TODO(Joao) check

    def test_raise_error(self):
        # TODO(Joao) This time we want to test if the error is correctly exectuted, when no answers file is loaded, but something is saved.
        #            If we do not load any file, we cannot save the answer of the textarea anywhere, thus an error is raised for the user
        #            The test is already written, but try to understand the logic here a bit
        assertTrue = self.assertTrue
        # @Joao this is a bit complicated, it is explained here https://github.com/agoscinski/scicode-widgets-unofficial/issues/2
        #       but its okay if you don't understand all the details
        class AssertRaiseOutput(SurpressStdOutput):
            def __exit__(self, etype, evalue, tb):
                super().__exit__(etype, evalue, tb)
                nonlocal assertTrue
                test_condition = etype is FileNotFoundError
                assertTrue(test_condition) # <--- checks if the correct has been executed
                return True
        self.textarea_answer._save_output = AssertRaiseOutput()
        self.textarea_answer._save_button.click() # <-- @Joao clicking the button calls a saving function which raises the error
    
    # TODO(Joao) all the tests are also valid for CodeDemo, can you do them for CodeDemo
    # If you want to not rewrite the whole test logic you can use the package `parametrized`
    # https://stackoverflow.com/questions/32899/how-do-you-generate-dynamic-parameterized-unit-tests-in-python
