"""
Piano Transcription Model - Extracted from training.ipynb
CRNN-based model for piano note transcription
"""

import os
import torch
import torch.nn as nn
import torch.nn.functional as F


class CRNN_OnsetsAndFrames_Original(nn.Module):
    """
    Original model architecture that matches the saved weights.
    Has 'classifier' instead of 'fc_frame' and different conv_block structure.
    """
    def __init__(self, num_pitches: int = 88, lstm_hidden_size: int = 256, cnn_out_channels: int = 128):
        super().__init__()
        self.name = "crnn_onsets_frames"
        self.num_pitches = num_pitches

        # Original convolutional feature extractor matching saved weights
        self.conv_block = nn.Sequential(
            # Layer 0,1: First conv block
            nn.Conv2d(1, 32, kernel_size=(3,3), padding=(1,1)),        # 0
            nn.BatchNorm2d(32),                                        # 1
            nn.ReLU(),                                                 # 2
            nn.MaxPool2d(kernel_size=(2,1)),                          # 3
            nn.Dropout2d(0.2),                                        # 4
            
            # Layer 5,6: Second conv block  
            nn.Conv2d(32, 64, kernel_size=(3,3), padding=(1,1)),      # 5
            nn.BatchNorm2d(64),                                       # 6
            nn.ReLU(),                                                # 7
            nn.MaxPool2d(kernel_size=(2,1)),                         # 8
            nn.Dropout2d(0.3),                                       # 9

            # Layer 10,11: Third conv block
            nn.Conv2d(64, cnn_out_channels, kernel_size=(3,3), padding=(1,1)),  # 10
            nn.BatchNorm2d(cnn_out_channels),                         # 11
            nn.ReLU(),                                                # 12
            nn.MaxPool2d(kernel_size=(2,1)),                         # 13
        )

        # Calculate LSTM input size after conv layers
        freq_out = 128 // 8  # = 16 after 3 pooling layers
        lstm_input_size = cnn_out_channels * freq_out

        self.lstm = nn.LSTM(
            input_size=lstm_input_size,
            hidden_size=lstm_hidden_size,
            num_layers=2,
            bidirectional=True,
            batch_first=False,
        )

        # Original classifier instead of fc_frame
        self.classifier = nn.Sequential(
            nn.Linear(2 * lstm_hidden_size, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_pitches)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x: [B, 128, T]  -> returns logits [B, 88, T]
        """
        if x.dim() != 3:
            raise ValueError(f"Expected input [B, 128, T], got {tuple(x.shape)}")

        # Add channel dim for convs: [B, 1, 128, T]
        x = x.unsqueeze(1)

        # Convolutional feature extraction
        x = self.conv_block(x)
        B, C, Freq, T = x.shape

        # Prepare sequence for LSTM: [T, B, C*F']
        x_seq = x.permute(3, 0, 1, 2).contiguous().view(T, B, C * Freq)

        # BiLSTM
        lstm_out, _ = self.lstm(x_seq)  # [T, B, 2*hidden]

        # Apply classifier to each time step
        # Reshape to [T*B, 2*hidden] for classification
        lstm_out_reshaped = lstm_out.view(T * B, -1)
        frame_logits = self.classifier(lstm_out_reshaped)  # [T*B, 88]
        
        # Reshape back to [T, B, 88] then -> [B, 88, T]
        frame_logits = frame_logits.view(T, B, self.num_pitches)
        return frame_logits.permute(1, 2, 0)


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
    Load a trained model from file with flexible architecture detection
    
    Args:
        model_path: path to saved model weights (.pth file or zip archive)
        device: torch device
        num_pitches: number of piano keys
    
    Returns:
        model: loaded model in eval mode
    """
    try:
        # Load checkpoint first to inspect structure
        checkpoint = torch.load(model_path, map_location=device, weights_only=False)
        
        # Handle different checkpoint formats
        if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
            state_dict = checkpoint['model_state_dict']
        elif isinstance(checkpoint, dict):
            state_dict = checkpoint
        else:
            raise ValueError("Unknown checkpoint format")
        
        # Check if this is the original model architecture (with classifier)
        has_classifier = any(key.startswith('classifier.') for key in state_dict.keys())
        
        if has_classifier:
            # Use the original model architecture that matches the saved weights
            print("🔍 Detected original model architecture with classifier")
            model = CRNN_OnsetsAndFrames_Original(num_pitches=num_pitches)
        else:
            # Use the current model architecture
            print("🔍 Detected current model architecture")
            model = create_model(device=device, num_pitches=num_pitches)
            return model
        
        model = model.to(device)
        model.load_state_dict(state_dict, strict=False)  # Allow partial loading
        model.eval()
        print(f"✅ Model loaded from {model_path}")
        return model
        
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        print("📝 Using randomly initialized weights instead")
        model = create_model(device=device, num_pitches=num_pitches)
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