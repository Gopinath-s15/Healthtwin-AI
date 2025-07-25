#!/usr/bin/env python3
"""
Model Training Pipeline for Enhanced Handwriting Recognition
"""

import torch
from torch.utils.data import Dataset, DataLoader
from transformers import TrOCRProcessor, VisionEncoderDecoderModel, Trainer, TrainingArguments
import cv2
import numpy as np
from PIL import Image
import logging
from pathlib import Path
from typing import List, Dict, Tuple
import json

logger = logging.getLogger(__name__)

class MedicalHandwritingDataset(Dataset):
    def __init__(self, samples: List[Dict], processor: TrOCRProcessor):
        self.samples = samples
        self.processor = processor
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        sample = self.samples[idx]
        
        # Load image
        image = Image.open(sample['image_path']).convert('RGB')
        
        # Process with TrOCR processor
        pixel_values = self.processor(image, return_tensors="pt").pixel_values.squeeze()
        
        # Tokenize text
        labels = self.processor.tokenizer(
            sample['text'],
            padding="max_length",
            max_length=64,
            truncation=True,
            return_tensors="pt"
        ).input_ids.squeeze()
        
        return {
            'pixel_values': pixel_values,
            'labels': labels
        }

class MedicalTrOCRTrainer:
    def __init__(self, model_name: str = "microsoft/trocr-base-handwritten"):
        self.model_name = model_name
        self.processor = TrOCRProcessor.from_pretrained(model_name)
        self.model = VisionEncoderDecoderModel.from_pretrained(model_name)
        
        # Configure for medical domain
        self.model.config.decoder_start_token_id = self.processor.tokenizer.cls_token_id
        self.model.config.pad_token_id = self.processor.tokenizer.pad_token_id
        self.model.config.vocab_size = self.model.config.decoder.vocab_size
    
    def fine_tune_on_medical_data(self, train_samples: List[Dict], val_samples: List[Dict]):
        """Fine-tune TrOCR on medical handwriting data"""
        
        # Create datasets
        train_dataset = MedicalHandwritingDataset(train_samples, self.processor)
        val_dataset = MedicalHandwritingDataset(val_samples, self.processor)
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir="./models/medical_trocr",
            per_device_train_batch_size=8,
            per_device_eval_batch_size=8,
            num_train_epochs=10,
            logging_steps=100,
            save_steps=500,
            evaluation_strategy="steps",
            eval_steps=500,
            save_total_limit=3,
            remove_unused_columns=False,
            push_to_hub=False,
            dataloader_pin_memory=False,
        )
        
        # Create trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            data_collator=self._data_collator,
        )
        
        # Start training
        logger.info("Starting medical TrOCR fine-tuning...")
        trainer.train()
        
        # Save model
        trainer.save_model()
        self.processor.save_pretrained("./models/medical_trocr")
        
        logger.info("Medical TrOCR fine-tuning completed")
    
    def _data_collator(self, batch):
        """Custom data collator for TrOCR training"""
        pixel_values = torch.stack([item['pixel_values'] for item in batch])
        labels = torch.stack([item['labels'] for item in batch])
        
        return {
            'pixel_values': pixel_values,
            'labels': labels
        }