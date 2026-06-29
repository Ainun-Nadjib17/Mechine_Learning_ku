import h5py
import json

def clean_config(d):
    if isinstance(d, dict):
        if 'dtype' in d and isinstance(d['dtype'], dict):
            # Replace DTypePolicy dict with simple string
            d['dtype'] = d['dtype'].get('config', {}).get('name', 'float32')
        if 'batch_shape' in d:
            d['batch_input_shape'] = d.pop('batch_shape')
        for v in d.values():
            clean_config(v)
    elif isinstance(d, list):
        for item in d:
            clean_config(item)

def fix_h5_full(file_path):
    with h5py.File(file_path, 'r+') as f:
        if 'model_config' not in f.attrs:
            print("No model_config found.")
            return
            
        config_str = f.attrs['model_config']
        if isinstance(config_str, bytes):
            config_str = config_str.decode('utf-8')
            
        model_config = json.loads(config_str)
        clean_config(model_config)
        
        f.attrs['model_config'] = json.dumps(model_config).encode('utf-8')
        print(f"Successfully cleaned and updated model_config in {file_path}")

fix_h5_full("brain_tumor_model.h5")
