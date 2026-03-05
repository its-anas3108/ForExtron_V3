"""
cnn_model.py – PyTorch 1D CNN for pattern recognition on candlestick sequences.
Conv1D layers detect local patterns (e.g., pin bars, inside candles).
"""

import torch
import torch.nn as nn
import numpy as np
import os
import logging
from app.config import settings

logger = logging.getLogger(__name__)
MODEL_PATH = os.path.join(settings.MODEL_DIR, "cnn_model.pt")


class _CNNNet(nn.Module):
    def __init__(self, input_dim: int, seq_len: int = 50):
        super().__init__()
        self.conv_block = nn.Sequential(
            # Conv1D expects (batch, channels=features, seq_len)
            nn.Conv1d(input_dim, 32, kernel_size=3, padding=1),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.MaxPool1d(2),                # seq_len → 25
            nn.Conv1d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.MaxPool1d(2),                # 25 → 12
            nn.Conv1d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(4),        # → 4
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128 * 4, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 1),
            nn.Sigmoid(),
        )

    def forward(self, x):
        # x: (batch, seq_len, features) → transpose to (batch, features, seq_len)
        x = x.permute(0, 2, 1)
        x = self.conv_block(x)
        return self.classifier(x).squeeze(-1)


class CNNModel:
    def __init__(self, input_dim: int = 42, seq_len: int = 50):
        self.input_dim = input_dim
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = _CNNNet(input_dim, seq_len).to(self.device)
        self._load()

    def _load(self):
        if os.path.exists(MODEL_PATH):
            self.model.load_state_dict(torch.load(MODEL_PATH, map_location=self.device))
            self.model.eval()
            logger.info("✅ CNN model loaded from disk")

    def predict(self, sequence: np.ndarray) -> float:
        self.model.eval()
        with torch.no_grad():
            x = torch.tensor(sequence, dtype=torch.float32).unsqueeze(0).to(self.device)
            return float(self.model(x).item())

    def train_model(self, X: np.ndarray, y: np.ndarray, epochs: int = 40, lr: float = 1e-3):
        self.model.train()
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=lr, weight_decay=1e-4)
        criterion = nn.BCELoss()

        X_t = torch.tensor(X, dtype=torch.float32).to(self.device)
        y_t = torch.tensor(y, dtype=torch.float32).to(self.device)

        for epoch in range(epochs):
            optimizer.zero_grad()
            loss = criterion(self.model(X_t), y_t)
            loss.backward()
            optimizer.step()
            if epoch % 10 == 0:
                logger.info(f"CNN Epoch {epoch}/{epochs} Loss: {loss.item():.4f}")
        self.save()

    def save(self):
        os.makedirs(settings.MODEL_DIR, exist_ok=True)
        torch.save(self.model.state_dict(), MODEL_PATH)
