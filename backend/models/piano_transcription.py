"""
Piano Transcription Model - Extracted from training.ipynb
CRNN-based model for piano note transcription
"""

import os
import torch
import torch.nn as nn
import torch.nn.functional as F


class CRNN_OnsetsAndFrames(nn.Module):
    """
    Input  (batch):  audio features shaped [B, 128, T]  (128 mel bins x T frames)
    Output (batch):  logits shaped      [B, 88,  T]     (88 piano keys x T frames)

    Notes
    -----
    - We keep time resolution by pooling only along the frequency axis (2,1).
    - We return *logits* (NO sigmoid) so that BCEWithLogitsLoss can be used correctly.
    """
    def __init__(self, num_pitches: int = 88, lstm_hidden_size: int = 256, cnn_out_channels: int = 128):
        super().__init__()
        self.name = "crnn_onsets_frames"
        self.num_pitches = num_pitches

        # Convolutional feature extractor (freq pooling only)
        self.conv_block = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=(3,3), padding=(1,1)),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=(2,1)),  # 128 -> 64

            nn.Conv2d(32, 64, kernel_size=(3,3), padding=(1,1)),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=(2,1)),  # 64 -> 32

            nn.Conv2d(64, cnn_out_channels, kernel_size=(3,3), padding=(1,1)),
            nn.BatchNorm2d(cnn_out_channels),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=(2,1)),  # 32 -> 16
        )

        # After 3x (2,1) pools, frequency dim: 128 -> 64 -> 32 -> 16
        freq_out = 128 // 8  # = 16
        lstm_input_size = cnn_out_channels * freq_out

        self.lstm = nn.LSTM(
            input_size=lstm_input_size,
            hidden_size=lstm_hidden_size,
            num_layers=2,
            bidirectional=True,
            batch_first=False,
        )

        # Residual projection to match BiLSTM output size (2 * hidden)
        self.res_fc = nn.Linear(lstm_input_size, 2 * lstm_hidden_size)

        # Frame-wise classifier to 88 piano keys
        self.fc_frame = nn.Linear(2 * lstm_hidden_size, num_pitches)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x: [B, 128, T]  -> returns logits [B, 88, T]
        """
        if x.dim() != 3:
            raise ValueError(f"Expected input [B, 128, T], got {tuple(x.shape)}")

        # Add channel dim for convs: [B, 1, 128, T]
        x = x.unsqueeze(1)

        # [B, C, F', T] with F' = 16
        x = self.conv_block(x)
        B, C, Freq, T = x.shape

        # Prepare sequence for LSTM: [T, B, C*F']
        x_seq = x.permute(3, 0, 1, 2).contiguous().view(T, B, C * Freq)

        # BiLSTM
        lstm_out, _ = self.lstm(x_seq)  # [T, B, 2*hidden]

        # Residual connection (project x_seq to BiLSTM size and add)
        lstm_out = lstm_out + self.res_fc(x_seq)

        # Frame-wise logits -> [T, B, 88] then -> [B, 88, T]
        frame_logits = self.fc_frame(lstm_out)
        return frame_logits.permute(1, 2, 0)


def create_model(device='cpu', num_pitches=88):
    """
    Create and initialize the piano transcription model
    
    Args:
        device: torch device ('cpu' or 'cuda')
        num_pitches: number of piano keys (default 88)
    
    Returns:
        model: initialized CRNN_OnsetsAndFrames model
    """
    model = CRNN_OnsetsAndFrames(num_pitches=num_pitches)
    model = model.to(device)
    model.eval()  # Set to evaluation mode by default
    return model


def load_model(model_path, device='cpu', num_pitches=88):
    """
    Load a trained model from file
    
    Args:
        model_path: path to saved model weights (.pth file or zip archive)
        device: torch device
        num_pitches: number of piano keys
    
    Returns:
        model: loaded model in eval mode
    """
    model = create_model(device=device, num_pitches=num_pitches)
    
    try:
        # Load checkpoint (works for both .pth and zip archives)
        checkpoint = torch.load(model_path, map_location=device, weights_only=False)
        
        # Handle different checkpoint formats
        if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
            # Full training checkpoint format
            state_dict = checkpoint['model_state_dict']
        elif isinstance(checkpoint, dict):
            # Assume direct state dict
            state_dict = checkpoint
        else:
            raise ValueError("Unknown checkpoint format")
            
        model.load_state_dict(state_dict)
        print(f"✅ Model loaded from {model_path}")
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        print("📝 Using randomly initialized weights instead")
    
    return model


def save_model(model, model_path):
    """
    Save model weights to file
    
    Args:
        model: the model to save
        model_path: path to save the model (.pth file)
    """
    try:
        torch.save(model.state_dict(), model_path)
        print(f"✅ Model saved to {model_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to save model: {e}")
        return False