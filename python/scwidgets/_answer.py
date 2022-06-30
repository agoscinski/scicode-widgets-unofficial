import os 
import json
import functools

from ipywidgets import (
    Output,
    Button,
    VBox,
    HBox,
    Layout,
    Text,
    Textarea
)


class Answer:
    """An interface for a widget which contains an answer for a question that can be saved to a file by the widget."""
    def __init__(self):
        self._save_output = Output()
        self._save_button = None
        self._on_save_callback = None

    @property
    def save_output(self):
        return self._save_output

    @property
    def answer_value(self):
        raise NotImplementedError("answer_value property has not been implemented.")

    @answer_value.setter
    def answer_value(self, new_answer_value):
        raise NotImplementedError("answer property setter has not been implemented.")

    def on_save(self):
        raise NotImplementedError("on_save has not been implemented.")

    def _init_save_widget(self, callback):
        self._save_button = Button(description="Save answer") 
        self._on_save_callback = callback
        self._save_button.on_click(self._on_save_callback)
        return VBox([self._save_button, self._save_output],
                layout=Layout(align_items="flex-start")
        )

    def _update_save_widget(self, callback):
        if self._save_button is not None and self._on_save_callback is not None:
            self._save_button.on_click(self._on_save_callback, remove=True)
            self._on_save_callback = callback
            self._save_button.on_click(self._on_save_callback)
        else:
            raise ValueError(f"Undefined state of save button: `self._save_button` is {self._save_button} and `self._on_save_callback` {self._on_save_callback}. Both should be None or not None")

class AnswerRegistry(VBox):
    """
    A widget to enter the name of the learner, and to save the state of registered widgets to a .json file, and load them back afterwards.    
    """
    @property
    def prefix(self):
        return self._prefix


    def __init__(self, prefix=None):
        self._prefix = prefix
        self._callbacks = {}

        self._load_answers_button = Button(description="Load")
        self._load_answers_button.on_click(self._load_answers)
        self._author_name_text = Text(description="Name")
        self._answer_widgets = {}
        self._answers_filename = None
        self._output = Output(layout=Layout(width='100%', height='100%'))
        super(AnswerRegistry, self).__init__(
                [HBox([self._author_name_text, self._load_answers_button]), self._output])

    def clear_output(self):
        self._output.clear_output()

    def _load_answers(self, change=""):
        """ Forces creation of answers file when not existing"""
        self.clear_output()
        if (self._prefix is None) or (self._prefix == ""):
            answers_base_filename = self._author_name_text.value.replace(" ","")
        else:
            answers_base_filename = self._prefix+"-"+self._author_name_text.value.replace(" ","")

        self._answers_filename = answers_base_filename + '.json'
        if not(os.path.exists(self._answers_filename)):
            with self._output:
                print(f"File {self._answers_filename} not found. Creating new file.")
            answers = {key: widget.answer_value for key, widget in self._answer_widgets.items()}
            with open(self._answers_filename, "w") as answers_file:
                json.dump(answers, answers_file)
        else:
            with open(self._answers_filename, "r") as answers_file:
                answers = json.load(answers_file)
                for answer_key, answer_value in answers.items():
                    if not answer_key in self._answer_widgets:
                        with self._output:
                            raise ValueError(f"Field ID {answer_key} in the data dump is not registered.")
                    self._answer_widgets[answer_key].answer_value = answer_value
        with self._output:
            print(f"Success: File {self._answers_filename} loaded.")

    def _save_answer(self, change, answer_key=None):
        if answer_key is None:
            raise ValueError("Cannot save answer with None answer_key")
        self._answer_widgets[answer_key].save_output.clear_output()
        if (self._answers_filename is None) or not(os.path.exists(self._answers_filename)):
            # outputs error at the widget where the save button is attached to
            with self._answer_widgets[answer_key].save_output:
                raise FileNotFoundError(f"No file has been loaded.")
        else:
            with open(self._answers_filename, "r") as answers_file:
                answers = json.load(answers_file)
            answers[answer_key] = self._answer_widgets[answer_key].answer_value
            with open(self._answers_filename, "w") as answers_file:
                json.dump(answers , answers_file)
            # outputs messagec at the widget where the save button is attached to
            with self._answer_widgets[answer_key].save_output:
                print(f"Success: Answer written to file {self._answers_filename}")
            return True
 
    def register_answer_widget(self, answer_key, widget):
        self._answer_widgets[answer_key] = widget

        if isinstance(widget, Answer):
            self._callbacks[answer_key] = functools.partial(self._save_answer, answer_key=answer_key)
            widget.on_save(self._callbacks[answer_key])
        else:
            raise ValueError(f"Widget {widget} is not of type {Answer.__name__}. Therefore does not support saving the of answer.")


class TextareaAnswer(VBox, Answer):
    """ A widget that contains a Textarea whose value can be saved"""
    def __init__(self, *args, **kwargs):
        self._answer_textarea = Textarea(*args, **kwargs)
        super(TextareaAnswer, self).__init__(
                [self._answer_textarea], layout=Layout(align_items="flex-start", width='100%'))

    @property
    def answer_value(self):
        return self._answer_textarea.value

    @answer_value.setter
    def answer_value(self, new_answer_value):
        self._answer_textarea.value = new_answer_value

    def on_save(self, callback):
        if self._save_button is None and self._on_save_callback is None:
            save_widget = self._init_save_widget(callback)
            self.children += (save_widget,)
        else:
            self._update_save_widget(self, callback)
