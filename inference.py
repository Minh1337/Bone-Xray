import json
from pathlib import Path
import numpy as np
import pandas as pd
import torch
import joblib
import albumentations as A
from albumentations.pytorch import ToTensorV2
from PIL import Image
import model_definition as definition

class Predictor:
    def __init__(self, folder, device='cpu'):
        folder = Path(folder)
        self.device = torch.device(device)
        ckpt = torch.load(folder/'best_model.pt',map_location='cpu',weights_only=False)
        definition.configure(ckpt['config'])
        self.labels = ckpt['flat_labels']
        self.model = definition.HierarchicalSwinCrossAttnLocalHeads(
            ckpt['metadata_dim'], ckpt['config']['use_metadata'])
        self.model.load_state_dict(ckpt['model_state'], strict=True)
        self.model.to(self.device).eval()
        state = joblib.load(folder/'metadata_processor.joblib')
        self.processor = definition.MetadataProcessor(state['meta_cols'])
        self.processor.colinfo = state['colinfo']; self.processor.fitted = state['fitted']
        self.transform = A.load(str(folder/'val_transform.json'))

    @torch.inference_mode()
    def predict(self, image_path, metadata):
        missing = set(self.processor.meta_cols)-set(metadata)
        if missing: raise ValueError(f'Missing metadata: {sorted(missing)}')
        if str(metadata['gender']).strip().upper() not in ['M','F']:
            raise ValueError('gender must be M/F')
        with Image.open(image_path) as im:
            image = np.array(im.convert('RGB'))
        x = self.transform(image=image)['image'].unsqueeze(0).to(self.device)
        meta = torch.from_numpy(self.processor.transform(pd.DataFrame([metadata]))).to(self.device)
        scores = self.model(x,meta)['flat'].softmax(1)[0].cpu().tolist()
        return sorted([{'label':label,'score':score} for label,score in zip(self.labels,scores)],
                      key=lambda item:item['score'],reverse=True)
