import torch
import torch.nn as nn
import torch.optim as optim
import logging
from tqdm import tqdm

try:
    from torch.cuda.amp import GradScaler, autocast
    HAS_AMP = True
except ImportError:
    HAS_AMP = False

logger = logging.getLogger(__name__)


class ForextronV3Trainer:
    """Trainer pipeline for Forextron v3 handling multi-head regression and classification losses."""
    
    def __init__(self, model, lr=1e-3, weight_decay=1e-5, device="cpu"):
        self.model = model
        self.device = torch.device(device)
        self.model.to(self.device)
        
        self.optimizer = optim.AdamW(self.model.parameters(), lr=lr, weight_decay=weight_decay)
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(self.optimizer, mode='min', patience=3, factor=0.5)
        
        # AMP for Mixed Precision
        self.scaler = GradScaler() if HAS_AMP and "cuda" in self.device.type else None
        
        # Losses
        # BCE treats direction/confidence as probability (0 to 1). The model outputs probabilities via sigmoid 
        # so we use BCELoss rather than BCEWithLogitsLoss to avoid double-sigmoid.
        self.bce_loss = nn.BCELoss()
        self.mse_loss = nn.MSELoss()

    def _compute_loss(self, outputs, targets):
        """
        Calculates a dynamically weighted combined multi-head loss.
        targets should be a dict: {
            "direction": tensor(B,),
            "confidence": tensor(B,),
            "return": tensor(B,),
            "volatility": tensor(B,)
        }
        """
        # Direction & Confidence (Classification / Probabilistic)
        loss_dir = self.bce_loss(outputs["direction"], targets["direction"].float())
        loss_conf = self.bce_loss(outputs["confidence"], targets["confidence"].float())
        
        # Return & Volatility (Regression)
        loss_ret = self.mse_loss(outputs["return"], targets["return"].float())
        loss_vol = self.mse_loss(outputs["volatility"], targets["volatility"].float())
        
        # Weighted combination 
        total_loss = (loss_dir * 1.0) + (loss_conf * 0.5) + (loss_ret * 2.0) + (loss_vol * 1.0)
        
        return total_loss, {
            "loss_dir": loss_dir.item(),
            "loss_conf": loss_conf.item(),
            "loss_ret": loss_ret.item(),
            "loss_vol": loss_vol.item()
        }

    def train_epoch(self, dataloader, epoch):
        self.model.train()
        total_loss = 0.0
        
        pbar = tqdm(dataloader, desc=f"Epoch {epoch} Training")
        for features, regime, targets in pbar:
            features = features.to(self.device)
            regime = regime.to(self.device)
            targets = {k: v.to(self.device) for k, v in targets.items()}
            
            self.optimizer.zero_grad()
            
            if self.scaler:
                with autocast():
                    outputs = self.model(features, regime)
                    loss, metrics = self._compute_loss(outputs, targets)
                
                self.scaler.scale(loss).backward()
                self.scaler.step(self.optimizer)
                self.scaler.update()
            else:
                outputs = self.model(features, regime)
                loss, metrics = self._compute_loss(outputs, targets)
                loss.backward()
                self.optimizer.step()
                
            total_loss += loss.item()
            pbar.set_postfix({"Loss": f"{loss.item():.4f}", "Dir": f"{metrics['loss_dir']:.4f}"})
            
        return total_loss / len(dataloader)

    def validate_epoch(self, dataloader):
        self.model.eval()
        total_loss = 0.0
        
        with torch.no_grad():
            for features, regime, targets in dataloader:
                features = features.to(self.device)
                regime = regime.to(self.device)
                targets = {k: v.to(self.device) for k, v in targets.items()}
                
                if self.scaler:
                    with autocast():
                        outputs = self.model(features, regime)
                        loss, _ = self._compute_loss(outputs, targets)
                else:
                    outputs = self.model(features, regime)
                    loss, _ = self._compute_loss(outputs, targets)
                    
                total_loss += loss.item()
                
        avg_loss = total_loss / len(dataloader)
        self.scheduler.step(avg_loss)
        return avg_loss
