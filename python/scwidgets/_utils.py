import inspect
import sys
import json
from ase import Atoms
import numpy as np

from ipywidgets import Output

# TODO(low) need to consider traits
def copy_widget(widget):
    signature = inspect.getfullargspec(type(widget).__init__)
    return type(widget)(*[getattr(widget, arg) for arg in signature.args[1:]])

class CustomAssertionError(Exception):
    def __init__(self, message, errors):            
        # Call the base class constructor with the parameters it needs
        super().__init__(message)
        # Now for your custom code...
        self.errors = errors


class Exercise:
    def __init__(self, checks):
        self._checks = checks

    @property
    def checks(self):
        return self._checks
        
    @checks.setter
    def checks(self, new_checks):
        self._checks = new_checks

    def __dict__(self):
        return {'checks': self._checks}
    
    def __str__(self):
        return self.__dict__().__str__()
    
    def __eq__(self, other):
        if len(self.checks) != len(other.checks):
            return False
        return all([self.checks[i] == other.checks[i] for i in range(len(self.checks))])

    def consistent(self, other):
        if len(self.checks) != len(other.checks):
            return False
        if len(self.checks) == 0:
            return True
        return all([self.checks[i].consistent( other.checks[i] ) for i in range(len(self.checks))])
    
class Check:
    def __init__(self, check_id=None, input_args=None, output_ref=None, assert_function=None, fingerprint_function=None, equal_function=None):
        self._check_id = check_id
        self._input_args = input_args
        self._output_ref = output_ref
        self._assert_function = assert_function
        self._fingerprint_function = fingerprint_function
        self._equal_function = equal_function
        
    @property
    def check_id(self):
        return self._check_id

    @property
    def input_args(self):
        return self._input_args

    @property
    def output_ref(self):
        return self._output_ref

    @property
    def assert_function(self):
        return self._assert_function

    @property
    def fingerprint_function(self):
        return self._fingerprint_function

    @property
    def equal_function(self):
        return self._equal_function

    
    def __dict__(self):
        return {'check_id': self._check_id,
                'input_args': self._input_args,
                'output_ref': self._output_ref, # None if self._output_ref is None else self._output_ref.__dict__(),
                'assert_function': self._assert_function,
                'fingerprint_function': self._fingerprint_function,
                'equal_function': self._equal_function}
    
    def __str__(self):
        return self.__dict__().__str__()

    def __eq__(self, other):
        return self.__dict__() == other.__dict__()

    def consistent(self, other):
        #print(self._input_args)
        #print(other._input_args)
        
        # does not have to be checked
        #if (self._output_ref is None) and (other._output_ref is None):
        #    consistency_output_ref = True
        #elif (self._output_ref is None) or (other._output_ref is None):
        #    consistency_output_ref = False
        #else:
        #    consistency_output_ref = self._output_ref.consistent(other._output_ref)
        
        #print("self._input_args", self._input_args)
        #print("other._input_args", other._input_args)
        # comparing dicts when one value is a np.array does not work
        # converting it to list before somehow works
        self_input_args = list(self._input_args.items())
        self_input_args.sort()
        other_input_args = list(other._input_args.items())
        other_input_args.sort()
        consistency_input_args = \
            JSON_ENCODER.encode(self_input_args) == JSON_ENCODER.encode(other_input_args)
        return all([
            self._check_id == other._check_id,
            consistency_input_args,
            #consistency_output_ref,
            self.consistent_function(self._assert_function, other._assert_function),
            self.consistent_function(self._fingerprint_function, other._fingerprint_function),
            self.consistent_function(self._equal_function, other._equal_function)
        ])
    @staticmethod
    def consistent_function(function1, function2):
        if isinstance(function1, str) and callable(function2):
            return function1 == function2.__name__
        elif isinstance(function2, str) and callable(function1):
            return function1.__name__ == function2
        else:
            return function1 == function2
        
class CheckableOutput: # Rename to OutputRef ?
    def __init__(self, meta_value, fingerprint):
        if not(isinstance(meta_value, MetaValue)):
            raise ValueError(f"meta_value {meta_value} must be of instance MetaValue.")
        self._meta_value = meta_value
        self._fingerprint = fingerprint
        
    @property
    def meta_value(self):
        return self._meta_value

    @property
    def fingerprint(self):
        return self._fingerprint
    
    def __dict__(self):
        return {'meta_value': self._meta_value,#None if self._meta_value is None else self._meta_value.__dict__(),
                'fingerprint': self._fingerprint}

    def __eq__(self, other):
        return all(self._fingerprint == other._fingerprint and self._meta_value == other._meta_value)
    
    def conistent(self, other):
        # value does not exist for student
        if self._fingerprint is not None:
            return (self._fingerprint == other._fingerprint) and (self._meta_value.consistent(other._meta_value))
        else:
            return self._meta_value.consistent(other._meta_value)
        
class MetaValue:
    def __init__(self, value):
        self._value = value
        self._meta = {}
        self._meta['type'] = value.__class__.__name__
        #print('hasattr(value, "__len__")',  hasattr(value, "__len__") )
        #if hasattr(value, "__len__"):
        #    print('value.__len__',  value.__len__ )
        #print("value.__class__.__name__", value.__class__.__name__)
        #print("value", value)
        
        # ndarray of size 0 have __len__ but return error
        try:
            self._meta['len'] = value.__len__()
        except:
            self._meta['len'] = None
        self._meta['shape'] = value.shape if hasattr(value, "shape") else None
        self._meta['dtype'] = value.dtype if hasattr(value, "dtype") else None
        
    def __dict__(self):
        return {'value': self._value, "meta": self._meta}
    
    @property
    def value(self):
        return self._value
    
    @property
    def meta(self):
        return self._meta
    
    def consistent(self, other):
        return self._meta == other._meta

class DefaultCheckJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        #print(obj)

        if isinstance(obj, type) or isinstance(obj, np.dtype):
            return obj.__str__()
        elif isinstance(obj, Exercise):
            arg = {key: self.default(val) for key, val in obj.__dict__().items()}
            #arg['module'] = 'builtins'
            #arg['type'] = 'dict'
            return {'arg': arg,
                    'module': str(obj.__class__.__module__),
                    'type': obj.__class__.__name__}
        elif isinstance(obj, Check):
            arg = {key: self.default(val) for key, val in obj.__dict__().items()}
            #arg['module'] = 'builtins'
            #arg['type'] = 'dict'
            return {'arg': arg,
                    'module': str(obj.__class__.__module__),
                    'type': obj.__class__.__name__}
        elif isinstance(obj, CheckableOutput):
            arg = {key: self.default(val) for key, val in obj.__dict__().items()}
            #arg['module'] = 'builtins'
            #arg['type'] = 'dict'
            obj_dump = {'arg': arg,
                    'module': str(obj.__class__.__module__),
                    'type': obj.__class__.__name__}
            # if fingerprint exists delete value in meta_value
            #print("obj_dump['arg']['fingerprint']['arg']", obj_dump['arg']['fingerprint']['arg'])
            if obj_dump['arg']['fingerprint']['arg'] != None:
                #print(obj_dump['arg']['meta_value']['arg'])
                obj_dump['arg']['meta_value']['arg']['value'] = None
                #print(obj_dump['arg']['meta_value'])
            return obj_dump
        elif isinstance(obj, MetaValue):
            # TODO put this back as soon as back decoder is able to do this
            #arg = {key: self.default(val) for key, val in obj.__dict__().items()}
            arg = {key: val for key, val in obj.__dict__().items()}
            return {'arg': arg,
                    'module': str(obj.__class__.__module__),
                    'type': obj.__class__.__name__}
        elif str(obj.__class__.__module__) == 'numpy' and type(obj).__name__ != 'function':
            arg =  obj.tolist() if obj.__class__.__name__ == "ndarray" else obj
            return {'arg': arg,
                    'module': str(obj.__class__.__module__),
                    'shape': str(obj.shape),
                    'dtype': str(obj.dtype),
                    'type': obj.__class__.__name__}
        elif str(obj.__class__.__module__) == 'ase.atoms':
            return {'arg': {'symbols': obj.symbols.__str__(), 'positions': obj.positions.tolist(), 'cell': obj.cell.tolist(), 'pbc': obj.pbc.tolist()},
                    'module': str(obj.__class__.__module__),
                    'type': obj.__class__.__name__}
        elif obj.__class__.__module__ == 'builtins':
            if obj.__class__.__name__ == 'function':
                return {'arg': obj.__name__,
                        'module': str(obj.__module__),
                        'type': obj.__class__.__name__}
            obj_dump = {'arg': obj,
                'module': str(obj.__class__.__module__),
                'type': obj.__class__.__name__}
            if hasattr(obj, '__len__'):
                obj_dump['len'] = len(obj)
            return obj_dump
        return super().default(obj)

class DefaultCheckJSONDecoder(json.JSONDecoder):
    # JSONDecoder decodes from string, this one does from str. have to refactor this a bit
    def decode(self, dct):
        # str -> dict -> obj
        
        # does not work with str, because 
        if isinstance(dct, str):
        #    print("str", dct)
            dct = super().decode(dct)
        if not(isinstance(dct, dict)):
            return dct
        #print("type found", dct.keys())
        #print("dct['type']", dct['type'] )
 
        if ('module' in dct.keys()) and (dct['module'] == 'builtins' or dct['module'] == '__main__'):
            if dct['type'] == 'function':
                if dct['module'] != '__main__':
                    #print(dct['module'], dct['arg'])
                    return eval(dct['module']+'.'+dct['arg'])
                else:
                    return dct['arg']
            elif dct['type'] == 'tuple':
                return tuple((self.decode(arg) for arg in dct['arg']))
            elif dct['type'] == 'NoneType':
                return None
            else:
                return self.decode(dct['arg'])
        elif 'type' in dct.keys():
            if dct['type'] == 'Exercise':
                #print( [self.decode(dct['arg']['checks']['arg'][i])
                #                for i in range(len(dct['arg']['checks']['arg']))] )
                return Exercise( [self.decode(dct['arg']['checks']['arg'][i])
                                for i in range(len(dct['arg']['checks']['arg']))] )
                #return Check( *[self.decode(arg) for arg in dct['arg'].values()] )
            elif dct['type'] == 'Check':
                #print("Check creation",  dct['arg'])
                #print([self.decode(arg) for arg in dct['arg'].values()])
                return Check( *[self.decode(arg) for arg in dct['arg'].values()] )
            elif dct['type'] == 'CheckableOutput':
                #print("[self.decode(arg) for arg in dct['arg'].values()]", [self.decode(arg) for arg in dct['arg'].values()])
                #print("CheckableOutput", CheckableOutput( *[self.decode(arg) for arg in dct['arg'].values()] ))
                #print("CheckableOutput.meta_value", CheckableOutput( *[self.decode(arg) for arg in dct['arg'].values()] ).meta_value)
                return CheckableOutput( *[self.decode(arg) for arg in dct['arg'].values()] )
            elif dct['type'] == 'MetaValue':
                #print(dct['arg'])
                if dct['arg']['value'] is None:
                    meta_value = MetaValue( None )
                    meta_value._meta = {}
                    meta_value.meta['type'] = dct['arg']['meta']['type']
                    meta_value.meta['len'] = dct['arg']['meta']['len'] if 'len' in dct['arg']['meta'].keys() else None
                    meta_value.meta['shape'] = tuple(dct['arg']['meta']['shape']) if ('shape' in dct['arg']['meta'].keys()) and (dct['arg']['meta']['shape'] is not None) else None
                    meta_value.meta['dtype'] = dct['arg']['meta']['dtype'] if 'dtype' in dct['arg']['meta'].keys() else None
                else:
                    meta_value = MetaValue( self.decode(dct['arg']['value']) )
                    meta_value.meta['type'] = dct['arg']['meta']['type']
                    meta_value.meta['len'] = dct['arg']['meta']['len'] if 'len' in dct['arg']['meta'].keys() else None
                    meta_value.meta['shape'] = tuple(dct['arg']['meta']['shape']) if ('shape' in dct['arg']['meta'].keys()) and (dct['arg']['meta']['shape'] is not None) else None
                    meta_value.meta['dtype'] = dct['arg']['meta']['dtype'] if 'dtype' in dct['arg']['meta'].keys() else None
                #print("meta_value.meta", meta_value.meta)
                return meta_value
            elif dct['module'] == 'numpy':
                # should cover cases like np.float64
                if dct['type'] == 'function':
                    return eval(f"np.{dct['arg']}")
                elif dct['type'] == 'ndarray':
                    #print("numpy", dct)
                    return np.array(dct['arg'], dtype=dct['dtype'])
                else:
                    return eval(f"np.{dct['type']}({dct['arg']})")
            elif dct['module'] == 'ase.atoms':
                return eval(f"Atoms(**{dct['arg']})")
        elif not('module' in dct.keys()): # these are dictionaries which are skipped in encoding
            return {key : arg for key, arg in dct.items()}
        return dct


class ConfigurableOutput(Output):
    def __init__(self, *args, suppress_std_out=False, suppress_std_err=False, **kwargs):
        self.suppress_std_err = suppress_std_err
        self.suppress_std_out = suppress_std_out
        self._file = None
        super().__init__(*args, **kwargs)

    def __enter__(self):
        super().__enter__()
        self.stdout = sys.stdout
        if self.suppress_std_out:
            self._file = open('/dev/null', 'w')
            sys.stdout = self._file

    def __exit__(self, etype, evalue, tb):
        super().__exit__(etype, evalue, tb)
        sys.stdout = self.stdout
        if self.suppress_std_out:
            self._file.close()
        if etype is None or self.suppress_std_err:
            return True
        return False

    def clear_output(self):
        super().clear_output()


JSON_ENCODER = DefaultCheckJSONEncoder()
JSON_DECODER = DefaultCheckJSONDecoder()
