import os 
import json
import functools
import glob

from ipywidgets import (
    Output,
    Button,
    VBox,
    HBox,
    Layout,
    Text,
    Textarea,
    Dropdown
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
        self._save_button = Button(description="Save answer", layout=Layout(width="200px", height="100%"))
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

    def is_valid_filename(self, filename):
        return ((self.prefix is not None and filename.startswith(self.prefix+"-") \
                or (self.prefix is None))) \
                and (filename.endswith("json"))

    @staticmethod
    def standardize_filename(filename):
        return filename.lower()

    def __init__(self, prefix=None):
        self._prefix = prefix
        #prefix must be lowercase in order to ensure files are correctly maintained (only lowercase)
        self._callbacks = {}
        self._current_path = os.getcwd()
        self._json_list = [filename for filename in
                map(os.path.basename, glob.glob(self._current_path + "/*.json"))
                if self.is_valid_filename(filename)]
        self._json_list.append("Create new answer file")
        self._answers_filename = None

        #Create/load/unload registry widgets
        self._student_name_text  = Text(placeholder='Enter your name here',  style= {'description_width': 'initial'})
        self._load_answers_button = Button(description='Load')
        self._save_answers_button = Button(description='Save all answers')
        self._create_savefile_button = Button(description='Create file')
        self._reload_button = Button(description='Choose another file')
        self._new_savefile = HBox([self._student_name_text, self._create_savefile_button])
        self._dropdown = Dropdown(
                            options=self._json_list,
                            description='Choose:',
                            disabled=False,
                        )
        self._savebox = HBox([self._dropdown, self._new_savefile]) \
                                if len(self._json_list) == 1 \
                                else HBox([self._dropdown, self._load_answers_button])

        self._current_dropdown_value = self._dropdown.value
        self._answer_widgets = {}
        self._preoutput = Output(layout=Layout(width='100%', height='100%'))
        self._output = Output(layout=Layout(width='100%', height='100%'))
        super(AnswerRegistry, self).__init__(
                [self._preoutput, self._savebox, self._output])

        #Stateful behavior:
        self._load_answers_button.on_click(self._load_answers)
        self._save_answers_button.on_click(self._save_all)
        self._create_savefile_button.on_click(self._create_savefile)
        self._dropdown.observe(self._on_choice,names='value')
        self._reload_button.on_click(self._enable_savebox)

        with self._preoutput:
            print("Please choose a save file and confirm before answering questions.")

    def clear_output(self):
        self._output.clear_output()

    def _on_choice(self,change=""):
        """
        a callback which observes _dropdown widget and proposes _new_savefile or _load_answers_button widgets depending on _current_dropdown_value
        """
        if change['new'][-5:-1] != change['old'][-5:-1]:
            if change['new'] == self._dropdown.options[-1]:
                self._savebox.children = [self._dropdown, self._new_savefile]
            else:
                self._savebox.children = [self._dropdown, self._load_answers_button]
        self._current_dropdown_value = change['new']


    def _load_answers(self, change=""):
        """
        loads registry when _load_answers_button is clicked
        """
        self.clear_output()
        self._answers_filename = self._current_dropdown_value
        error_occured = False
        with open(self._answers_filename, "r") as answers_file:
            answers = json.load(answers_file)
            for answer_key, answer_value in answers.items():
                if not answer_key in self._answer_widgets:
                    with self._output:
                        error_occured = True
                        # TODO improve message and restrict error trace to this ValueError
                        raise ValueError(f"Your json file contains unexpected Answer with key : {answer_key}.  ")
                else:
                    self._answer_widgets[answer_key].answer_value = answer_value
        if not error_occured:
            self._disable_savebox()
            self.children = [HBox([self._savebox, self._save_answers_button, self._reload_button]), self._output]
            with self._output:
                print(f"\033[92m File '{self._answers_filename}' loaded successfully.")

    def _verify_valid_student_name(self):
        if AnswerRegistry.is_name_empty(self._student_name_text.value):
            self.clear_output()
            # TODO we should we classify prints and so we can give them styles
            with self._output:
                print(f"\033[91m Your name is empty. Please provide a new one.")
            return False

        forbidden_characters = AnswerRegistry.extract_forbidden_characters(self._student_name_text.value)
        if len(forbidden_characters) > 0:
            self.clear_output()
            with self._output:
                print(f"\033[91m The name '{self._student_name_text.value}' contains invalid special characters {forbidden_characters}. Please provide another name.")
            return False

        return True

    def _create_savefile(self, change=""):
        """
        creates a new registry when _new_savefile_button is clicked
        """
        # Checks that the name is valid. If invalid, erase the name.

        if not(self._verify_valid_student_name()):
            return

        # if prefix is defined, it is added to the filename
        answers_filename = ""
        if (self._prefix is not None):
            answers_filename += self.prefix + "-"
        answers_filename += AnswerRegistry.standardize_filename(self._student_name_text.value) + ".json"

        if os.path.exists(answers_filename):
            self.clear_output()
            with self._output:
                print(f"\033[91m The name '{self._student_name_text.value.lower()}' is already used in file '{answers_filename}'. Please provide a new one.")
        else:
            self._answers_filename = answers_filename
            answers = {key: widget.answer_value for key, widget in self._answer_widgets.items()}
            with open(self._answers_filename, "w") as answers_file:
                json.dump(answers, answers_file)
            self._disable_savebox()
            self._json_list = list(dict.fromkeys([self._answers_filename] + self._json_list))
            self._dropdown.options = self._json_list
            self.children = [self._savebox, self._reload_button, self._output]
            self.clear_output()
            with self._output:
                print(f"\033[92m File {self._answers_filename} successfully created and loaded.")

    def _save_answer(self, change=None, answer_key=None):
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
            # outputs message at the widget where the save button is attached to
            with self._answer_widgets[answer_key].save_output:
                print(f"The answer was successfully recorded in '{self._answers_filename}'")
            return True

    @staticmethod
    def is_name_empty(name):
        return len(name) == name.count(" ")

    @staticmethod
    def extract_forbidden_characters(name):
        character_list = []
        forbidden_characters = "./\\"
        for character in forbidden_characters:
            if character in name:
                character_list += character
        return character_list

    def _disable_savebox(self):
        self._create_savefile_button.disabled = True
        self._load_answers_button.disabled = True
        self._dropdown.disabled = True
        self._student_name_text.disabled = True

    def _enable_savebox(self, change=""):
        # clean old states
        self._answers_filename = None
        #self._json_list = [os.path.basename(path)
        #        for path in glob.glob(self._current_path + "/*.json")
        #            if (os.path.basename(path).startswith(self.prefix+"-")
        #                and self.prefix != "") or (self.prefix == "")]
        self._json_list = [filename for filename in
                map(os.path.basename, glob.glob(self._current_path + "/*.json"))
                if self.is_valid_filename(filename)]
        self._json_list.append("Create new answer file")
        self._create_savefile_button.disabled = False
        self._load_answers_button.disabled = False
        self._dropdown.disabled = False
        self._student_name_text.disabled = False
        self.children = [self._savebox, self._output]
        self.clear_output()
        
        # clears output in each answer when another registry is loaded
        for key, answer_widget in self._answer_widgets.items() : 
            answer_widget.save_output.clear_output()

    def _save_all(self, change=""):
        for key in self._answer_widgets.keys(): 
            self._save_answer(answer_key=key, change="")

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
            self._update_save_widget(callback)
