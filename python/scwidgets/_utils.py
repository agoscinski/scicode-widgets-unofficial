import inspect
import enum

# TODO(low) need to consider traits
def copy_widget(widget):
    signature = inspect.getfullargspec(type(widget).__init__)
    return type(widget)(*[getattr(widget, arg) for arg in signature.args[1:]])

#TODO move somewhere more meaningful
class CodeDemoStatus(enum.Enum):
    UPDATING = 0
    UP_TO_DATE = 1
    OUT_OF_DATE = 2
    CHECKING = 3
    CHECKED = 4
    UNCHECKED = 5
