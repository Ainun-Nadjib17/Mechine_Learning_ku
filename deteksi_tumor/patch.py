import h5py
import json

def fix_h5(file_path):
    with h5py.File(file_path, 'r+') as f:
        model_config = json.loads(f.attrs.get('model_config'))
        
        layers = model_config.get('config', {}).get('layers', [])
        modified = False
        for layer in layers:
            if layer.get('class_name') == 'InputLayer':
                config = layer.get('config', {})
                if 'batch_shape' in config:
                    print(f"Found 'batch_shape' in InputLayer. Changing to 'batch_input_shape' in {file_path}")
                    config['batch_input_shape'] = config.pop('batch_shape')
                    modified = True
                    
        if modified:
            f.attrs['model_config'] = json.dumps(model_config).encode('utf-8')
            print("Successfully updated model_config in", file_path)
        else:
            print("No 'batch_shape' found or already fixed.")

fix_h5("brain_tumor_model.h5")
