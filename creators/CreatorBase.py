
from abc import abstractmethod

import copy
import os

def base_path():
    return os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    
def to_walltime(dt):
    """
    @type dt: timedelta
    @param dt: Walltime parameter in timedelta format.
    @rtype: string
    @return: dt converted to "DD:HH:MM:SS"
    """
    n_days = dt.days
    n_hours = dt.seconds // 3600
    n_mins = (dt.seconds // 60 ) % 60
    n_secs = dt.seconds % 60
    return "{:02d}:{:02d}:{:02d}:{:02d}".format(n_days,n_hours,n_mins,n_secs)

class ParamDescriptor:
    """
    Information describing a paramter.
    """
    def __init__(self, 
                 name, 
                 description, 
                 index, 
                 required=True, 
                 default_value=None, 
                 parser=None,
                 suggested_values=None):
        """
        Create a new ParamDescriptor
        
        @type name: string
        @param name: The parameter's name.
        @type description: string
        @param description: The parameter's description.
        @type index: int
        @param index: Index of this descriptor in a given set of descriptors.
        @type required: boolean
        @param required: Whether or not the user is required to provide this parameter.
        @type default_value: the parameter's type, or convertible by parser
        @param default_value: A default value for this parameter.
        @type parser: functor
        @param parser: Function for processing parameter values into standard form.
        @type suggested_values: list or functor
        @param suggested_values: List or function for generating list of suggested values.
        """
        self.name = name
        self.description = description
        self.index = index
        self.required = required
        self.default_value = default_value
        if (default_value is not None) and (parser is not None):
            self.default_value = parser(default_value)
        self.parser = parser
        self.suggested_values = suggested_values # used for generating templates
        
    def __str__(self): 
        required_str = ('required' if self.required else 'optional')
        default_value_str = ("\n    default_value: {:s}".format(str(self.default_value)) if self.default_value is not None else "")
        return '{:s} - {:s}\n    {:s}{:s}'.format(self.name,required_str,self.description,default_value_str)
        
def create_choice_descriptor(name,
                             choices,
                             description_prefix,
                             index,
                             required=True,
                             default_value=None):
    return  ParamDescriptor(name,
                            "{:s} {:s}.".format(description_prefix,print_choice_list(choices)),
                            0,
                            required,
                            default_value,
                            lambda x: x if x in choices else None,
                            choices)

def print_choice_list(choices):
    str = "('{:s}'".format(choices[0])
    for x in choices[1:]:
        str = "{:s}|'{:s}'".format(str,x)
    str = "{:s})".format(str)
    return str

class Params:
    """
    Base class for dictionary-based params with json serialization.
    """
   
    def __init__(self, schema, values = {}):
        """
        Initialize a Params object with values.
        
        @type values: dict of param_name, param_value
        @param values: User's parameter values.
        """
        self.__schema = schema
        self.__values = {}
        for param_name, param_value in values.items():
            self.set(param_name,param_value)
        
    def __str__(self):
        result = 'Values:\n\n'
        for pair in self.__sorted_values(): 
            result += "{:s}: {:s}\n".format(pair[0],pair[1])
        result += '\nDescriptors:\n\n'
        for descriptor in self.__sorted_descriptors():
            result += "{:s}\n\n".format(descriptor)
        return result
        
    def schema(self):
        """
        Returns a deep copy of the schema. (A Params schema cannot be modified, but others 
        may need to inspect it.)
        
        @rtype: dict of ParamDescriptors
        @return: Deep copy of this Params object's schema.
        """
        return copy.deepcopy(self.__schema)
    
    def get(self, param_name, return_default=True): 
        if param_name in self.__values:
            return self.__values[param_name]
        elif return_default and (param_name in self.__schema):
            descriptor = self.__schema[param_name]
            return descriptor.default_value
        return None            
  
    def set(self, param_name, param_value):
        if param_name in self.__schema:
            descriptor = self.__schema[param_name]
            if descriptor.parser is not None:
                self.__values[param_name] = descriptor.parser(param_value)
            else:
                self.__values[param_name] = param_value
            self.__refresh_schema()
        else:
            raise RuntimeError("{:s} is not a valid parameter.".format(param_name))
    
    def clear(self, param_name): 
        if param_name in self.__values:
            del self.__values[param_name]
  
    def to_json(self): pass
  
    def save(self, path): pass
  
    def json_template(self): pass
  
    def save_template(self, path): pass
  
    @abstractmethod
    def load(path): pass
  
    def valid(self): 
        for param_name, descriptor in self.__schema.items():
            if descriptor.required:
                if param_name not in self.__values:
                    return False
        return True
    
    def __nonzero__(self): 
        return self.valid()
        
    def __sorted_values(self): 
        return sorted(self.__values.items(), key=lambda pair: self.__schema[pair[0]].index)
    
    def __sorted_descriptors(self): 
        return sorted(self.__schema.values(), key=lambda descriptor: descriptor.index)  
        
    def __refresh_schema(self):
        return

class Creator:

    def __init__(self, out_dir, params, resources_dir = None):
        self.out_dir = os.path.realpath(out_dir)
        self.params = params
        self.resources_dir = resources_dir
        if not self.params.valid():
            raise RuntimeError("Cannot create glm files with invalid parameters:\n{:s}".format(self.params))
        
    @abstractmethod
    def create(self): pass
        
