"""
transformer_model.py – PyTorch Transformer encoder for time-series (advanced accuracy booster).
Uses multi-head self-attention to capture long-range candle dependencies.
"""

import torch
import torch.nn as nn
import numpy as np
import os
import math
import logging
from app.config import settings

logger = logging.getLogger(__name__)
MODEL_PATH = os.path.join(settings.MODEL_DIR, "transformer_model.pt")


class _PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, max_len: int = 500, dropout: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(dropout)
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len).unsqueeze(1).float()
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # (1, max_len, d_model)
        self.register_buffer("pe", pe)

    def forward(self, x):
        x = x + self.pe[:, : x.size(1), :]
        return self.dropout(x)


class _TransformerNet(nn.Module):
    def __init__(self, input_dim: int, d_model: int = 64, nhead: int = 4,
                 num_layers: int = 3, dropout: float = 0.2):
        super().__init__()
        self.input_proj = nn.Linear(input_dim, d_model)
        self.pos_enc = _PositionalEncoding(d_model, dropout=dropout)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=nhead, dim_feedforward=128,
            dropout=dropout, batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.classifier = nn.Sequential(
            nn.Linear(d_model, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 1),
            nn.Sigmoid(),
        )

    def forward(self, x):
        # x: (batch, seq_len, input_dim)
        x = self.input_proj(x)
        x = self.pos_enc(x)
        x = self.transformer(x)
        x = x[:, -1, :]  # Use last token as classification summary
        return self.classifier(x).squeeze(-1)


class TransformerModel:
    def __init__(self, input_dim: int = 42):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = _TransformerNet(input_dim).to(self.device)
        self._load()

    def _load(self):
        if os.path.exists(MODEL_PATH):
            self.model.load_state_dict(torch.load(MODEL_PATH, map_location=self.device))
            self.model.eval()
            logger.info("✅ Transformer model loaded from disk")

    def predict(self, sequence: np.ndarray) -> float:
        self.model.eval()
        with torch.no_grad():
            x = torch.tensor(sequence, dtype=torch.float32).unsqueeze(0).to(self.device)
            return float(self.model(x).item())

    def train_model(self, X: np.ndarray, y: np.ndarray, epochs: int = 40, lr: float = 5e-4):
        self.model.train()
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=lr, weight_decay=1e-4)
        scheduler = torch.optim.lr_scheduler.OneCycleLR(
            optimizer, max_lr=lr, total_steps=epochs
        )
        criterion = nn.BCELoss()

        X_t = torch.tensor(X, dtype=torch.float32).to(self.device)
        y_t = torch.tensor(y, dtype=torch.float32).to(self.device)

        for epoch in range(epochs):
            optimizer.zero_grad()
            loss = criterion(self.model(X_t), y_t)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            if epoch % 10 == 0:
                logger.info(f"Transformer Epoch {epoch}/{epochs} Loss: {loss.item():.4f}")
        self.save()

    def save(self):
        os.makedirs(settings.MODEL_DIR, exist_ok=True)
        torch.save(self.model.state_dict(), MODEL_PATH)
