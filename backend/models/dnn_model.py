"""
dnn_model.py – PyTorch Deep Neural Network for directional probability prediction.
Architecture: Dense(128) → BatchNorm → ReLU → Dropout(0.3) → Dense(64) → ReLU → Dense(1) → Sigmoid
"""

import torch
import torch.nn as nn
import numpy as np
import os
import logging
from app.config import settings

logger = logging.getLogger(__name__)
MODEL_PATH = os.path.join(settings.MODEL_DIR, "dnn_model.pt")


class _DNNNet(nn.Module):
    def __init__(self, input_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid(),
        )

    def forward(self, x):
        return self.net(x).squeeze(-1)


class DNNModel:
    def __init__(self, input_dim: int = 42):
        self.input_dim = input_dim
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = _DNNNet(input_dim).to(self.device)
        self._load()

    def _load(self):
        if os.path.exists(MODEL_PATH):
            self.model.load_state_dict(torch.load(MODEL_PATH, map_location=self.device))
            self.model.eval()
            logger.info("✅ DNN model loaded from disk")

    def predict(self, feature_vector: np.ndarray) -> float:
        self.model.eval()
        with torch.no_grad():
            x = torch.tensor(feature_vector, dtype=torch.float32).unsqueeze(0).to(self.device)
            return float(self.model(x).item())

    def train_model(self, X: np.ndarray, y: np.ndarray, epochs: int = 50, lr: float = 1e-3):
        self.model.train()
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=lr, weight_decay=1e-4)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
        criterion = nn.BCELoss()

        X_t = torch.tensor(X, dtype=torch.float32).to(self.device)
        y_t = torch.tensor(y, dtype=torch.float32).to(self.device)

        for epoch in range(epochs):
            optimizer.zero_grad()
            preds = self.model(X_t)
            loss = criterion(preds, y_t)
            loss.backward()
            optimizer.step()
            scheduler.step()
            if epoch % 10 == 0:
                logger.info(f"DNN Epoch {epoch}/{epochs} Loss: {loss.item():.4f}")

        self.save()

    def save(self):
        os.makedirs(settings.MODEL_DIR, exist_ok=True)
        torch.save(self.model.state_dict(), MODEL_PATH)
