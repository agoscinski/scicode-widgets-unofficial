import unittest
import sys

from IPython.display import display
import ipywidgets

from widget_code_input import WidgetCodeInput
from scwidgets import (CodeDemo, CodeChecker, ParametersBox, PyplotOutput, TextareaAnswer, AnswerRegistry)

import matplotlib.pyplot as plt
import matplotlib
# same backend as in jupyter notebook
matplotlib.use('module://ipympl.backend_nbagg')

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

    def test_load_answers(self):
        # TODO(Joao) create new file with AnswerRegistry using the load_button, set _author_name_text to some value then use the .click() function of the load button
        # then check for one registered widget that the answer key can be found in the the json without having clicked on the save button of the widget
        self.answer_registry._author_name_text.value = "Max Mustermann"
        self.answer_registry.register_answer_widget("textarea_key", self.textarea_answer)
        self.answer_registry._load_answers_button.click()
        # the file test-MaxMustermann.json exists now, here a check just to show you, can be deleted
        import os
        print(os.listdir("./"))
        #print(os.path.exists("test-MaxMustermann.json"))
        # are all keys present 

    def test_answer_correctly_saved(self):
        # TODO(Joao) so here something similar as in the above text, now check set the value in the textarea_answer to s.th. and check if it is stored after clicking on the save button

        self.answer_registry._author_name_text.value = "Max Mustermann"
        self.answer_registry.register_answer_widget("textarea_key", self.textarea_answer)
        self.answer_registry._ipython_display_()
        #self.textarea_answer.answer_value = ... TODO
        self.answer_registry._load_answers_button.click()

        self.textarea_answer._save_button.click()
        # load the saved json file and check value of "textarea_key" 

    def test_raise_error(self):
        # TODO(Joao) This time we want to test if the error is correctly exectuted. For that we have self.assertRaises, read some documentation for it and tr
        # textarea has no
        self.answer_registry._author_name_text.value = "Max Mustermann"
        self.answer_registry.register_answer_widget("textarea_key", self.textarea_answer)
        # because we are running the tests not in a jupyter notebook but in a terminal, we have to display the widget differently. We need to display the widget
        # so that clicking on the button actually executes the code we have set it up to execute.
        self.textarea_answer.save_output._ipython_display_()
        display(self.textarea_answer)
        # this time we do not load any file, so we cannot save the answer in the textarea anywhere and an error is raised 
        self.textarea_answer._save_button.click() # <-- raises error make test out of this
    
    @testbook('./my_notebook.ipynb')
    def test_get_details(tb):
        tb.inject(
            """
            import mock
            mock_client = mock.MagicMock()
            mock_df = pd.DataFrame()
            mock_df['week'] = range(10)
            mock_df['count'] = 5
            p1 = mock.patch.object(bigquery, 'Client', return_value=mock_client)
            mock_client.query().result().to_dataframe.return_value = mock_df
            p1.start()
            """,
            before=2,
            run=False
        )
        tb.execute()
        dataframe = tb.get('dataframe')
        assert dataframe.shape == (10, 2)

        x = tb.get('x')
        assert x == 7


    # TODO(Joao) all the tests are also valid for CodeCheck, you can reuse the existing tests using parametrized
    # https://stackoverflow.com/questions/32899/how-do-you-generate-dynamic-parameterized-unit-tests-in-python
