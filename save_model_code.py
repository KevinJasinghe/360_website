#!/usr/bin/env python3
"""
Model saving code to add after your training loop
"""
import torch
import os

# Add this code after your training loop completes
print(f"Aggressive training final error: {train_errors_agg[-1]:.6f}")

# ===== ADD THIS CODE TO SAVE THE MODEL =====

# Create weights directory if it doesn't exist
weights_dir = "weights"
os.makedirs(weights_dir, exist_ok=True)

# Save the trained model weights
model_path = os.path.join(weights_dir, "piano_transcription_weights.pth")
torch.save(overfit_model_b.state_dict(), model_path)
print(f"✅ Model weights saved to: {model_path}")

# Also save full model info for debugging
full_model_path = os.path.join(weights_dir, "piano_transcription_full.pth")
torch.save({
    'model_state_dict': overfit_model_b.state_dict(),
    'final_train_loss': train_losses_agg[-1] if train_losses_agg else None,
    'final_train_error': train_errors_agg[-1] if train_errors_agg else None,
    'model_architecture': 'CRNN_OnsetsAndFrames',
    'training_info': {
        'epochs': 150,
        'lr': 5e-3,
        'overfit_size': 5,
        'batch_size': 5
    }
}, full_model_path)
print(f"✅ Full model info saved to: {full_model_path}")

# Verify the files exist
if os.path.exists(model_path):
    file_size = os.path.getsize(model_path) / (1024 * 1024)  # MB
    print(f"📊 Model file size: {file_size:.2f} MB")
else:
    print("❌ Model save failed!")