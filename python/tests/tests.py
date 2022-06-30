import unittest
import sys
import os
import json

from IPython.display import display
from IPython.core.interactiveshell import InteractiveShell

from widget_code_input import WidgetCodeInput
from scwidgets import (CodeDemo, CodeChecker, ParametersBox, PyplotOutput, TextareaAnswer, AnswerRegistry)

import matplotlib.pyplot as plt
import matplotlib
# same backend as in jupyter notebook
matplotlib.use('module://ipympl.backend_nbagg')


class SurpressStdOutput():
    def __init__(self):
        pass
    def __enter__(self):
        self.stdout = sys.stdout
        sys.stdout = None
        pass
    def __exit__(self, etype, evalue, tb):
        sys.stdout = self.stdout
        if etype is None:
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
        self.failing_code_input = WidgetCodeInput(
                function_name="test",
                function_parameters="a",
                docstring="",
                function_body="return b")
        self.test_code_checker = CodeChecker({(1,):(2,), (2,):(3,)})

        self.test_code_demo = CodeDemo(code_input=self.working_code_input,
                    input_parameters_box=None,
                    visualizers=None,
                    update_on_input_parameter_change=False,
                    update_visualizers=None,
                    code_checker=self.test_code_checker,
                    separate_check_and_update_buttons=False)

        self.parbox = ParametersBox(a11 = (1., -4, 4, 0.1, r'$a_{11} / Å$'),
                      a12 = (0., -4, 4, 0.1, r'$a_{12} / Å$'),
                      a21 = (0., -4, 4, 0.1, r'$a_{21} / Å$'),
                      a22 = (2., -4, 4, 0.1, r'$a_{22} / Å$'))

    def test_nb_checks(self):
        assert self.test_code_checker.nb_checks == 2

    def test_code_checker_check(self):
        self.test_code_checker.check(self.working_code_input)
        self.assertRaises(NameError, self.test_code_checker.check, self.failing_code_input)

    def test_code_demo_display(self):
        # tests if on_displayed callback works properly
        foo_was_run = False
        def foo(a, code_input):
            nonlocal foo_was_run
            foo_was_run = True
        self.test_code_demo._update_visualizers = foo
        # simulates display(self.test_code_demo)
        #self.test_code_demo.update()
        orig_out = sys.stdout
        try: 
            sys.stdout = None
            self.test_code_demo._ipython_display_()
            sys.stdout = orig_out
        except e:
            sys.stdout = orig_out
            raise e
        self.assertTrue(foo_was_run)

    def test_code_demo_check(self):
        self.test_code_demo.check()

    def test_code_demo_check_click(self):
        self.test_code_demo.check_button.click()

    #def test_pyplot_output(self):
    #    # TODO(alex) gives a lot of deprecation warnings fix this before uncommenting test
    #    test_fig = plt.figure()
    #    PyplotOutput(test_fig)

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
