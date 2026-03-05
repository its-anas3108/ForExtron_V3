"""
gru_model.py – PyTorch GRU sequence model for temporal pattern learning.
Input: (batch, seq_len=50, features)
Output: bullish probability [0,1]
"""

import torch
import torch.nn as nn
import numpy as np
import os
import logging
from app.config import settings

logger = logging.getLogger(__name__)
MODEL_PATH = os.path.join(settings.MODEL_DIR, "gru_model.pt")


class _GRUNet(nn.Module):
    def __init__(self, input_dim: int, hidden: int = 64):
        super().__init__()
        self.gru1 = nn.GRU(input_dim, hidden, batch_first=True)
        self.drop1 = nn.Dropout(0.3)
        self.gru2 = nn.GRU(hidden, 32, batch_first=True)
        self.drop2 = nn.Dropout(0.2)
        self.fc = nn.Sequential(
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid(),
        )

    def forward(self, x):
        out, _ = self.gru1(x)
        out = self.drop1(out)
        out, _ = self.gru2(out)
        out = self.drop2(out[:, -1, :])   # Take last time step
        return self.fc(out).squeeze(-1)


class GRUModel:
    def __init__(self, input_dim: int = 42):
        self.input_dim = input_dim
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = _GRUNet(input_dim).to(self.device)
        self._load()

    def _load(self):
        if os.path.exists(MODEL_PATH):
            self.model.load_state_dict(torch.load(MODEL_PATH, map_location=self.device))
            self.model.eval()
            logger.info("✅ GRU model loaded from disk")

    def predict(self, sequence: np.ndarray) -> float:
        """sequence shape: (seq_len, features)"""
        self.model.eval()
        with torch.no_grad():
            x = torch.tensor(sequence, dtype=torch.float32).unsqueeze(0).to(self.device)
            return float(self.model(x).item())

    def train_model(self, X: np.ndarray, y: np.ndarray, epochs: int = 40, lr: float = 1e-3):
        """X shape: (N, seq_len, features), y shape: (N,)"""
        self.model.train()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        criterion = nn.BCELoss()

        X_t = torch.tensor(X, dtype=torch.float32).to(self.device)
        y_t = torch.tensor(y, dtype=torch.float32).to(self.device)

        for epoch in range(epochs):
            optimizer.zero_grad()
            loss = criterion(self.model(X_t), y_t)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
            optimizer.step()
            if epoch % 10 == 0:
                logger.info(f"GRU Epoch {epoch}/{epochs} Loss: {loss.item():.4f}")
        self.save()

    def save(self):
        os.makedirs(settings.MODEL_DIR, exist_ok=True)
        torch.save(self.model.state_dict(), MODEL_PATH)
