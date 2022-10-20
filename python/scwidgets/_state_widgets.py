import enum
import ipywidgets

class CodeDemoStatus(enum.Enum):
    """
    These enumes describe the status of a custom Widget related to the CodeDemo. The usual status flows are:
    update status flow
      UP_TO_DATE -- user change --> OUT_OF_DATE -- update initiated --> UPDATING -- update finishes --> UP_TO_DATE
    check status flow
      CHECKED -- user change --> UNCHECKED -- check initiated --> CKECKING -- update finishes --> CHECKED
    """
    UPDATING = 0
    UP_TO_DATE = 1
    OUT_OF_DATE = 2
    CHECKING = 3
    CHECKED = 4
    UNCHECKED = 5

class AnswerStatus(enum.Enum):
    """
    """
    SAVED = 0
    UNSAVED = 1

class LoadingImage(ipywidgets.Image):
    """
    Custom image supporting visual changes depending on status of CodeDemo

    Parameters
    ----------
        code_demo_functionality : str, no default
            Describes to which functionality of the code demo the widget belongs.
            Supported are: "update", "check" "check_update", no default
    """
    def __init__(self, **kwargs):
        if 'code_demo_functionality' not in kwargs:
            raise ValueError(f"Could not initiate {self.__class__.__name__}: no code_demo_functionality was given.")
        self._code_demo_functionality = kwargs.pop('code_demo_functionality')
        self.add_class("scwidget-loading-image")
        super().__init__(**kwargs)

    # for observe
    def set_status_unchecked(self, change=None):
        self.status = CodeDemoStatus.UNCHECKED

    # for observe
    def set_status_out_of_date(self, change=None):
        self.status = CodeDemoStatus.OUT_OF_DATE

    @property
    def status(self):
        return self._status if hasattr(self, "_status") else None

    @status.setter
    def status(self, status):
        # at the moment updating and checking are treated the same way
        # so we can use updating style also for checking
        # this migh however change in the future 
        if status == CodeDemoStatus.UPDATING:
            self.add_class("scwidget-loading-image--updating")
        elif status == CodeDemoStatus.UP_TO_DATE :
            self.remove_class("scwidget-loading-image--updating")
        elif status == CodeDemoStatus.OUT_OF_DATE:
            pass
        elif status == CodeDemoStatus.CHECKING:
            self.add_class("scwidget-loading-image--checking")
        elif status == CodeDemoStatus.CHECKED:
            self.remove_class("scwidget-loading-image--checking")
        elif status == CodeDemoStatus.UNCHECKED:
            pass
        elif not(isinstance(status, CodeDemoStatus)):
            raise ValueError(f"Status {status} is not a CodeDemoStatus.")
        else:
            raise ValueError(f'CodeDemoStatus {status} is not supported by {self.__class__.__name__}.')
        self._status = status

    def set_status(self, status):
        self.status = status

class CodeDemoButton(ipywidgets.Button):
    """
    Custom button supporting visual changes depending on status of CodeDemo

    Parameters
    ----------
        code_demo_functionality : str, no default
            Describes to which functionality of the code demo the widget belongs.
            Supported are: "update", "check" "check_update", no default
    """
    def __init__(self, **kwargs):
        if 'code_demo_functionality' not in kwargs:
            raise ValueError(f"Could not initiate {self.__class__.__name__}: no code_demo_functionality was given.")
        self._code_demo_functionality = kwargs.pop('code_demo_functionality')
        if self._code_demo_functionality not in ["update", "check", "check_update", "save"]:
            raise ValueError(f"Could not initiate {self.__class__.__name__}: not supported code_demo_functionality was given {self.code_demo_functionality}.")
        self.add_class("scwidget-button")
        super().__init__(**kwargs)

    @property
    def status(self):
        return self._status if hasattr(self, "_status") else None

    @status.setter
    def status(self, status):
        if self._code_demo_functionality == "update":
            if status == CodeDemoStatus.UPDATING:
                self.disabled = True
                self.remove_class("scwidget-button--out-of-date")
            elif status == CodeDemoStatus.UP_TO_DATE:
                self.disabled = True
                self.remove_class("scwidget-button--out-of-date")
            elif status == CodeDemoStatus.OUT_OF_DATE:
                self.disabled = False
                self.add_class("scwidget-button--out-of-date")
            elif isinstance(status, CodeDemoStatus):
                raise ValueError(f'CodeDemoStatus {status} is not supported by update {__self.__class__.__name__}.')
            elif not(isinstance(status, CodeDemoStatus)):
                raise ValueError(f"Status {status} is not a CodeDemoStatus.")
        elif self._code_demo_functionality == "check":
            if status == CodeDemoStatus.CHECKING:
                self.disabled = True
                self.remove_class("scwidget-button--unchecked")
            elif status == CodeDemoStatus.CHECKED:
                self.disabled = True
                self.remove_class("scwidget-button--unchecked")
            elif status == CodeDemoStatus.UNCHECKED:
                self.disabled = False
                self.add_class("scwidget-button--unchecked")
            elif isinstance(status, CodeDemoStatus):
                raise ValueError(f'CodeDemoStatus {status} is not supported by check {__self.__class__.__name__}.')
            elif not(isinstance(status, CodeDemoStatus)):
                raise ValueError(f"Status {status} is not a CodeDemoStatus.")
        elif self._code_demo_functionality == "check_update":
            if status == CodeDemoStatus.CHECKING or status == CodeDemoStatus.UPDATING:
                self.disabled = True
                self.remove_class("scwidget-button--out-of-date")
            elif status == CodeDemoStatus.CHECKED or status == CodeDemoStatus.UP_TO_DATE:
                self.disabled = True
                self.remove_class("scwidget-button--out-of-date")
            elif status == CodeDemoStatus.UNCHECKED or status == CodeDemoStatus.OUT_OF_DATE:
                self.disabled = False
                self.add_class("scwidget-button--out-of-date")
            elif isinstance(status, CodeDemoStatus):
                raise ValueError(f'CodeDemoStatus {status} is not supported by check_update {__self.__class__.__name__}.')
            elif not(isinstance(status, CodeDemoStatus)):
                raise ValueError(f"Status {status} is not a CodeDemoStatus.")
        elif self._code_demo_functionality == "save":
            if status == AnswerStatus.SAVED:
                self.disabled = True
                self.remove_class("scwidget-button--unsaved")
            elif status == AnswerStatus.UNSAVED:
                self.disabled = False
                self.add_class("scwidget-button--unsaved")
            elif isinstance(status, AnswerStatus):
                raise ValueError(f'AnswerStatus {status} is not supported by save {__self.__class__.__name__}.')
            elif not(isinstance(status, AnswerStatus)):
                raise ValueError(f"Status {status} is not a AnswerStatus.")
        else:
            raise ValueError(f"{__self.__class__.__name__} wrongly initialized. code_demo_functionality {self.code_demo_functionality} is not supported.")
        self._status = status

    def set_status(self, status):
        self.status = status

    # for observe
    def set_status_unchecked(self, change=None):
        self.status = CodeDemoStatus.UNCHECKED

    # for observe
    def set_status_out_of_date(self, change=None):
        self.status = CodeDemoStatus.OUT_OF_DATE

    # for observe
    def set_answer_status_unsaved(self, change=None):
        self.status = AnswerStatus.UNSAVED

# TODO  CodeDemoWidgets are not consistent with each other when setting status
#       make everywhere raise error if status is not supposed to be received
class SaveOutput(ipywidgets.Output):
    """
    Custom box supporting visual changes depending on status of CodeDemo

    Parameters
    ----------
        code_demo_functionality : str, no default
            Describes to which functionality of the code demo the widget belongs.
            Supported are: "update", "check" "check_update", no default
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


    # for observe
    def set_answer_status_unsaved(self, change=None):
        self.status = AnswerStatus.UNSAVED

    @property
    def status(self):
        return self._status if hasattr(self, "_status") else None

    @status.setter
    def status(self, status):
        if status == AnswerStatus.SAVED:
            pass
        elif status == AnswerStatus.UNSAVED:
            self.clear_output()
        elif isinstance(status, AnswerStatus):
            raise ValueError(f'AnswerStatus {status} is not supported by save {__self.__class__.__name__}.')
        else:
            raise ValueError(f"Status {status} is not a AnswerStatus.")
        self._status = status

    def set_status(self, status):
        self.status = status


class CodeDemoBox(ipywidgets.Box):
    """
    Custom box supporting visual changes depending on status of CodeDemo

    Parameters
    ----------
        code_demo_functionality : str, no default
            Describes to which functionality of the code demo the widget belongs.
            Supported are: "update", "check" "check_update", no default
    """
    def __init__(self, **kwargs):
        if 'code_demo_functionality' not in kwargs:
            raise ValueError("Could not initiate CodeDemoButton: no code_demo_functionality was given")
        self._code_demo_functionality = kwargs.pop('code_demo_functionality')
        if self._code_demo_functionality not in ["update", "check", "check_update", "save"]:
            raise ValueError(f"Could not initiate {self.__class__.__name__}: not supported code_demo_functionality was given {self.code_demo_functionality}.")
        self.add_class("scwidget-box")
        super().__init__(**kwargs)

    # for observe
    def set_status_unchecked(self, change=None):
        self.status = CodeDemoStatus.UNCHECKED

    # for observe
    def set_status_out_of_date(self, change=None):
        self.status = CodeDemoStatus.OUT_OF_DATE

    # for observe
    def set_answer_status_unsaved(self, change=None):
        self.status = AnswerStatus.UNSAVED

    @property
    def status(self):
        return self._status if hasattr(self, "_status") else None

    @status.setter
    def status(self, status):
        if self._code_demo_functionality == "check":
            if status == CodeDemoStatus.CHECKED:
                self.remove_class("scwidget-box--unchecked")
            elif status == CodeDemoStatus.UNCHECKED:
                self.add_class("scwidget-box--unchecked")
            elif status == CodeDemoStatus.CHECKING:
                self.remove_class("scwidget-box--unchecked")
            elif (isinstance(status, CodeDemoStatus)):
                raise ValueError(f'CodeDemoStatus {status} is not supported by check {__self.__class__.__name__}.')
            elif not(isinstance(status, CodeDemoStatus)):
                raise ValueError(f"Status {status} is not a CodeDemoStatus.")
        elif self._code_demo_functionality == "update":
            if status == CodeDemoStatus.UP_TO_DATE:
                self.remove_class("scwidget-box--out-of-date")
            elif status == CodeDemoStatus.OUT_OF_DATE:
                self.add_class("scwidget-box--out-of-date")
            elif status == CodeDemoStatus.UPDATING:
                self.remove_class("scwidget-box--out-of-date")
            elif (isinstance(status, CodeDemoStatus)):
                raise ValueError(f'CodeDemoStatus {status} is not supported by update {__self.__class__.__name__}.')
            elif not(isinstance(status, CodeDemoStatus)):
                raise ValueError(f"Status {status} is not a CodeDemoStatus.")
        elif self._code_demo_functionality == "check_update":
            if status == CodeDemoStatus.UP_TO_DATE:
                self.remove_class("scwidget-box--out-of-date")
            elif status == CodeDemoStatus.OUT_OF_DATE:
                self.add_class("scwidget-box--out-of-date")
            elif status == CodeDemoStatus.UPDATING:
                self.remove_class("scwidget-box--out-of-date")
            elif status == CodeDemoStatus.CHECKING or status == CodeDemoStatus.CHECKED or status == CodeDemoStatus.UNCHECKED:
                pass
            elif (isinstance(status, CodeDemoStatus)):
                raise ValueError(f'CodeDemoStatus {status} is not supported by check_update {__self.__class__.__name__}.')
            elif not(isinstance(status, CodeDemoStatus)):
                raise ValueError(f"Status {status} is not a CodeDemoStatus.")
        elif self._code_demo_functionality == "save":
            if status == AnswerStatus.SAVED:
                self.remove_class("scwidget-box--unsaved")
            elif status == AnswerStatus.UNSAVED:
                self.add_class("scwidget-box--unsaved")
            elif (isinstance(status, AnswerStatus)):
                raise ValueError(f'AnswerStatus {status} is not supported by check {__self.__class__.__name__}.')
            elif not(isinstance(status, AnswerStatus)):
                raise ValueError(f"Status {status} is not a AnswerStatus.")
        else:
            raise ValueError(f"{__self.__class__.__name__} wrongly initialized. code_demo_functionality {self.code_demo_functionality} is not supported.")
        self._status = status

    def set_status(self, status):
        self.status = status
