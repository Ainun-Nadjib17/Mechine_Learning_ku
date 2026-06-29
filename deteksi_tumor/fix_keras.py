import zipfile
import json
import os
import shutil

try:
    # Step 1: extract all to a temporary dir
    os.makedirs('tmp_keras', exist_ok=True)
    with zipfile.ZipFile('brain_tumor_model.keras', 'r') as z:
        z.extractall('tmp_keras')

    # Step 2: Read config.json
    with open('tmp_keras/config.json', 'r') as f:
        config = json.load(f)

    # Step 3: Modify config.json (deep search)
    def replace_batch_shape(d):
        if isinstance(d, dict):
            if 'batch_shape' in d:
                d['batch_input_shape'] = d.pop('batch_shape')
            for k, v in d.items():
                replace_batch_shape(v)
        elif isinstance(d, list):
            for item in d:
                replace_batch_shape(item)

    replace_batch_shape(config)

    with open('tmp_keras/config.json', 'w') as f:
        json.dump(config, f)

    # Step 4: Zip it back
    backup = 'brain_tumor_model_fixed.keras'
    with zipfile.ZipFile(backup, 'w') as z:
        for root, dirs, files in os.walk('tmp_keras'):
            for file in files:
                z.write(os.path.join(root, file), arcname=os.path.relpath(os.path.join(root, file), 'tmp_keras'))

    shutil.rmtree('tmp_keras')
    print("Fixed keras model generated as", backup)
except Exception as e:
    print("Error:", e)
