import unittest
import sys

from IPython.display import display
import ipywidgets

from widget_code_input import WidgetCodeInput
from scwidgets import (CodeDemo, CodeChecker, ParametersBox, PyplotOutput)

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('module://ipympl.backend_nbagg')

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
                    code_visualizers=None,
                    update_on_input_parameter_change=False,
                    process_code=None,
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
        self.test_code_demo.process_code = foo
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
    #    # TODO gives a lot of deprecation warnings fix this before uncommenting test
    #    test_fig = plt.figure()
    #    PyplotOutput(test_fig)
