
import numpy as np
from hashlib import blake2b
import json
import os


xopt_logo = """  _   
                | |  
__  _____  _ __ | |_ 
\ \/ / _ \| '_ \| __|
 >  < (_) | |_) | |_ 
/_/\_\___/| .__/ \__|
          | |        
          |_|        
"""




#--------------------------------
# VOCS utilities
def save_vocs(vocs_dict, filePath=None):
    """
    Write VOCS dictionary to a JSON file. 
    If no filePath is given, the name is chosen from the 'name' key + '.json'
    """

    if filePath:
        name = filePath
    else:
        name = vocs_dict['name']+'.json'
    with open(name, 'w') as outfile:
        json.dump(vocs_dict, outfile, ensure_ascii=True, indent='  ')
    print(name, 'written')
    
    
def load_vocs(filePath):
    """
    Load VOCS from a JSON file
    Returns a dict
    """
    with open(filePath, 'r') as f:
        dat = json.load(f)
    return dat    
    


def random_settings(vocs, include_constants=True, include_linked_variables=True):
    """
    Uniform sampling of the variables described in vocs['variables'] = min, max.
    Returns a dict of settings. 
    If include_constants, the vocs['constants'] are added to the dict. 
    
    """
    settings = {}
    for key, val in vocs['variables'].items():
        a, b = val
        x = np.random.random()
        settings[key] = x*a + (1-x)*b
        
    # Constants    
    if include_constants:
        settings.update(vocs['constants'])
        
    # Handle linked variables
    if include_linked_variables and 'linked_variables' in vocs:
        for k, v in vocs['linked_variables'].items():
            settings[k] = settings[v]
        
    return settings    

def random_settings_arrays(vocs, n, include_constants=True, include_linked_variables=True):
    """
    Similar to random_settings, but with arrays of size n. 
    
    Uniform sampling of the variables described in vocs['variables'] = min, max.
    Returns a dict of settings, with each settings as an array. 

    If include_constants, the vocs['constants'] are added to the dict as full arrays.
    
    """
    settings = {}
    for key, val in vocs['variables'].items():
        a, b = val
        x = np.random.random(n)
        settings[key] = x*a + (1-x)*b
        
    # Constants    
    if include_constants:
        for k, v in vocs['constants'].items():
            settings[k] = np.full(n, v)
        
    # Handle linked variables
    if include_linked_variables and 'linked_variables' in vocs:
        for k, v in vocs['linked_variables'].items():
            settings[k] = np.full(n, settings[v])
        
    return settings    




#--------------------------------
# Vector encoding and decoding
    
# Decode vector to dict
def decode1(vec, labels):
    return dict(zip(labels, vec.tolist()))
# encode dict to vector
def encode1(d, labels):
    return [d[key] for key in labels]    
    

#--------------------------------
# Paths
    
def full_path(path, ensure_exists=True):
    """
    Makes path abolute. Can ensure exists. 
    """
    p = os.path.expandvars(path)
    p = os.path.abspath(p)
    if ensure_exists:
        assert os.path.exists(p), 'path does not exist: '+p
    return p

def add_to_path(path, prepend=True):
    """
    Add path to $PATH
    """
    p = full_path(path)
    
    if prepend:
        os.environ['PATH']  = p+os.pathsep+os.environ['PATH']
    else:
        # just append
        os.environ['PATH']  += os.pathsep+p
    return p    
    
    
#--------------------------------
# h5 utils

def write_attrs(h5, group_name, data):
    """
    Simple function to write dict data to attribues in a group with name
    """
    g = h5.create_group(group_name)
    for key in data:
        g.attrs[key] = data[key]
    return g



def write_attrs_nested(h5, name, data):
    """
    Recursive routine to write nested dicts to attributes in a group with name 'name'
    """
    if type(data) == dict:
        g = h5.create_group(name)
        for k, v in data.items():
            write_attrs_nested(g, k, v)
    else:
        h5.attrs[name] = data    
        
        
#--------------------------------
# data fingerprinting   
class NumpyEncoder(json.JSONEncoder):
    """
    See: https://stackoverflow.com/questions/26646362/numpy-array-is-not-json-serializable
    """
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)
def fingerprint(keyed_data, digest_size=16):
    """
    Creates a cryptographic fingerprint from keyed data. 
    Used JSON dumps to form strings, and the blake2b algorithm to hash.
    
    """
    h = blake2b(digest_size=16)
    for key in keyed_data:
        val = keyed_data[key]
        s = json.dumps(val, sort_keys=True, cls=NumpyEncoder).encode()
        h.update(s)
    return h.hexdigest()          