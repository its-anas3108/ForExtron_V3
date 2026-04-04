import torch
import torch.nn as nn
import torch.nn.functional as F

# ──────────────────────────────────────────────────────────────────────────────
# 1. Gated Residual Network (GRN)
# ──────────────────────────────────────────────────────────────────────────────
class GLU(nn.Module):
    """Gated Linear Unit"""
    def __init__(self, input_size):
        super(GLU, self).__init__()
        self.fc1 = nn.Linear(input_size, input_size)
        self.fc2 = nn.Linear(input_size, input_size)

    def forward(self, x):
        return self.fc1(x) * torch.sigmoid(self.fc2(x))


class GRN(nn.Module):
    """Gated Residual Network for robust feature filtering"""
    def __init__(self, input_size, hidden_size, output_size, dropout=0.1):
        super(GRN, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.elu = nn.ELU()
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.dropout = nn.Dropout(dropout)
        self.gate = GLU(hidden_size)
        self.layer_norm = nn.LayerNorm(output_size)
        
        if input_size != output_size:
            self.skip_proj = nn.Linear(input_size, output_size)
        else:
            self.skip_proj = None

    def forward(self, x):
        residual = x
        x = self.fc1(x)
        x = self.elu(x)
        x = self.fc2(x)
        x = self.dropout(x)
        x = self.gate(x)
        
        if self.skip_proj is not None:
            residual = self.skip_proj(residual)
            
        x = x + residual
        return self.layer_norm(x)

# ──────────────────────────────────────────────────────────────────────────────
# 2. PatchTST Module
# ──────────────────────────────────────────────────────────────────────────────
class PatchTSTBlock(nn.Module):
    """Divides sequence into patches and extracts local relationships entirely independent of RNNs."""
    def __init__(self, seq_len: int, patch_len: int, num_features: int, d_model: int, n_heads: int, tf_dropout: float):
        super(PatchTSTBlock, self).__init__()
        self.seq_len = seq_len
        self.patch_len = patch_len
        self.num_patches = seq_len // patch_len
        
        # Linear projection from raw patch size (num_features * patch_len) to d_model
        self.patch_proj = nn.Linear(patch_len * num_features, d_model)
        
        # Learnable position embeddings for patches
        self.position_embedding = nn.Parameter(torch.randn(1, self.num_patches, d_model))
        
        # Transformer Encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, 
            nhead=n_heads, 
            dropout=tf_dropout, 
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=2)

    def forward(self, x):
        # x: (batch_size, seq_len, num_features)
        batch_size = x.size(0)
        
        # Reshape to patches: (batch_size, num_patches, patch_len * num_features)
        x_patched = x.view(batch_size, self.num_patches, self.patch_len * x.size(2))
        
        # Project patches to d_model: (batch_size, num_patches, d_model)
        x_proj = self.patch_proj(x_patched)
        
        # Add positional embedding
        x_proj = x_proj + self.position_embedding
        
        # Transform
        out = self.transformer(x_proj) # (batch_size, num_patches, d_model)
        return out

# ──────────────────────────────────────────────────────────────────────────────
# 3. Temporal Convolutional Network (TCN)
# ──────────────────────────────────────────────────────────────────────────────
class Chomp1d(nn.Module):
    """Causal padding slice"""
    def __init__(self, chomp_size):
        super(Chomp1d, self).__init__()
        self.chomp_size = chomp_size

    def forward(self, x):
        return x[:, :, :-self.chomp_size].contiguous()


class TemporalBlock(nn.Module):
    def __init__(self, n_inputs, n_outputs, kernel_size, stride, dilation, padding, dropout=0.2):
        super(TemporalBlock, self).__init__()
        self.conv1 = nn.Conv1d(n_inputs, n_outputs, kernel_size,
                               stride=stride, padding=padding, dilation=dilation)
        # Apply causal padding by removing rightmost padding
        self.chomp1 = Chomp1d(padding)
        self.relu1 = nn.ReLU()
        self.dropout1 = nn.Dropout(dropout)

        self.conv2 = nn.Conv1d(n_outputs, n_outputs, kernel_size,
                               stride=stride, padding=padding, dilation=dilation)
        self.chomp2 = Chomp1d(padding)
        self.relu2 = nn.ReLU()
        self.dropout2 = nn.Dropout(dropout)

        self.net = nn.Sequential(self.conv1, self.chomp1, self.relu1, self.dropout1,
                                 self.conv2, self.chomp2, self.relu2, self.dropout2)
        
        # Residual connection
        self.downsample = nn.Conv1d(n_inputs, n_outputs, 1) if n_inputs != n_outputs else None
        self.relu = nn.ReLU()

    def forward(self, x):
        out = self.net(x)
        res = x if self.downsample is None else self.downsample(x)
        return self.relu(out + res)


class TemporalConvNet(nn.Module):
    """Extracts temporal stability over patched multi-head dependencies."""
    def __init__(self, num_inputs, num_channels, kernel_size=2, dropout=0.2):
        super(TemporalConvNet, self).__init__()
        layers = []
        num_levels = len(num_channels)
        for i in range(num_levels):
            dilation_size = 2 ** i
            in_channels = num_inputs if i == 0 else num_channels[i-1]
            out_channels = num_channels[i]
            layers.append(TemporalBlock(
                in_channels, out_channels, kernel_size, stride=1, dilation=dilation_size,
                padding=(kernel_size-1) * dilation_size, dropout=dropout
            ))
        self.network = nn.Sequential(*layers)

    def forward(self, x):
        # x is (batch_size, num_patches, d_model) -> reshape for 1D conv (batch_size, d_model, num_patches)
        x = x.transpose(1, 2)
        y = self.network(x)
        # Reverse back to (batch_size, num_patches, d_model)
        return y.transpose(1, 2)

# ──────────────────────────────────────────────────────────────────────────────
# 4. Temporal Fusion Transformer Architecture (Forextron v3)
# ──────────────────────────────────────────────────────────────────────────────
class ForextronV3(nn.Module):
    """
    Forextron v3: State-of-the-Art Temporal Architecture
    - Feature Embedding
    - PatchTST (Local Attention)
    - TCN (Causal Dilation)
    - TFT (Global Attention)
    - Regime Embeddings
    - GRN
    - Multi-Head Output (Sigmoid & Linear Extrapolations)
    """
    def __init__(
        self, 
        num_features: int,
        seq_len: int = 64,
        patch_len: int = 8,
        num_regimes: int = 4,
        d_model: int = 64,
        tcn_channels: list = [64, 64],
        n_heads: int = 4,
        dropout: float = 0.1
    ):
        super(ForextronV3, self).__init__()
        
        assert seq_len % patch_len == 0, "Sequence length must be precisely divisible by patch length."
        
        # Feature embeddings mapping strictly across raw structured dimension
        self.feature_embed = nn.Linear(num_features, d_model)
        
        # Patch Time Series Transformer
        self.patch_tst = PatchTSTBlock(
            seq_len=seq_len, 
            patch_len=patch_len, 
            num_features=d_model, 
            d_model=d_model, 
            n_heads=n_heads, 
            tf_dropout=dropout
        )
        
        # Temporal Convolutional Network
        self.tcn = TemporalConvNet(
            num_inputs=d_model, 
            num_channels=tcn_channels, 
            kernel_size=2, 
            dropout=dropout
        )
        
        # Temporal Fusion Transformer Attention Layer
        tcn_out_dim = tcn_channels[-1]
        self.tft_attention = nn.MultiheadAttention(
            embed_dim=tcn_out_dim, 
            num_heads=n_heads, 
            dropout=dropout, 
            batch_first=True
        )
        
        # Market Regime Learnable Injection Array
        self.regime_embedding = nn.Embedding(num_embeddings=num_regimes, embedding_dim=tcn_out_dim)
        
        # Gated Residual Post-Network Filters
        self.grn = GRN(
            input_size=tcn_out_dim * 2, # Context + Regime
            hidden_size=tcn_out_dim, 
            output_size=tcn_out_dim, 
            dropout=dropout
        )
        
        # Multi-Head Decision Output Ensembles
        self.direction_head = nn.Linear(tcn_out_dim, 1)    
        self.confidence_head = nn.Linear(tcn_out_dim, 1)   
        self.return_head = nn.Linear(tcn_out_dim, 1)       
        self.volatility_head = nn.Linear(tcn_out_dim, 1)   

    def forward(self, features, regime):
        """
        features: (B, L, F) where L=64, F=num_features
        regime: (B,) scalar indices mapping to contraction/expansion
        """
        # 1. Feature Embedding
        # Apply elementwise numerical embedding to dense representation
        x = self.feature_embed(features) # (B, L, d_model)
        
        # 2. PatchTST Block (Local sequence segmentation via non-recurrent transformers)
        x = self.patch_tst(x) # (B, N, d_model)

        # 3. Sequence Causal Dilations via TCN
        x = self.tcn(x) # (B, N, tcn_out_dim)
        
        # 4. Temporal Fusion Sequence Attention
        # Global query is the temporally furthest stable state (last memory block)
        idx_seq_last = x[:, -1:, :] # (B, 1, tcn_out_dim)
        attn_out, _ = self.tft_attention(idx_seq_last, x, x)
        attn_out = attn_out.squeeze(1) # (B, tcn_out_dim)
        
        # 5. Regime Dynamic Injection
        r_emb = self.regime_embedding(regime) # (B, tcn_out_dim)
        combined = torch.cat([attn_out, r_emb], dim=1) # (B, 2*tcn_out_dim)
        
        # 6. Structurally Filter
        grn_out = self.grn(combined) # (B, tcn_out_dim)
        
        # 7. Disperse to Multi-Heads Output Metrics
        direction = torch.sigmoid(self.direction_head(grn_out)).squeeze(-1)
        confidence = torch.sigmoid(self.confidence_head(grn_out)).squeeze(-1)
        exp_return = self.return_head(grn_out).squeeze(-1)
        volatility = F.softplus(self.volatility_head(grn_out)).squeeze(-1)
        
        return {
            "direction": direction,
            "confidence": confidence,
            "return": exp_return,
            "volatility": volatility
        }
