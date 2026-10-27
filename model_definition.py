import torch
import torch.nn as nn
import torch.nn.functional as F
import timm
import numpy as np
import pandas as pd
from types import SimpleNamespace
from sklearn.preprocessing import StandardScaler, OneHotEncoder

CFG = None
NUM_FLAT = 10

def configure(config):
    global CFG
    CFG = SimpleNamespace(**config)
    CFG.pretrained = False

class MetadataProcessor:
    def __init__(self, meta_cols):
        self.meta_cols = list(meta_cols)
        self.colinfo   = {}
        self.fitted    = False

    def fit(self, df):
        self.colinfo = {}
        for col in self.meta_cols:
            low = col.lower()
            if low == 'gender':
                self.colinfo[col] = {'type': 'gender'}
                continue
            num  = pd.to_numeric(df[col], errors='coerce')
            uniq = set(num.dropna().unique().tolist())
            if uniq.issubset({0, 1, 0.0, 1.0}):
                self.colinfo[col] = {'type': 'binary', 'fill': 0.0}
            elif num.notna().mean() >= 0.5:
                fill   = float(num.median()) if num.notna().sum() else 0.0
                scaler = StandardScaler().fit(num.fillna(fill).values.reshape(-1, 1))
                self.colinfo[col] = {'type': 'numeric', 'fill': fill, 'scaler': scaler}
            else:
                vals = df[col].fillna('MISSING').astype(str).str.strip().values.reshape(-1, 1)
                ohe  = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
                ohe.fit(vals)
                self.colinfo[col] = {'type': 'categorical', 'ohe': ohe}
        self.fitted = True
        return self

    def transform(self, df):
        if not self.fitted:
            raise RuntimeError('MetadataProcessor must be fitted first')
        parts = []
        for col in self.meta_cols:
            info = self.colinfo[col]
            if info['type'] == 'gender':
                # 1 cột duy nhất: 1.0 = Male, 0.0 = Female.
                # Không dùng fillna vì data không có missing.
                # Không tạo 2-3 cột vì M + F = 1 luôn -> dummy variable trap.
                g   = df[col].astype(str).str.strip().str.upper()
                arr = (g == 'M').astype(np.float32).values.reshape(-1, 1)
                parts.append(arr)
            elif info['type'] == 'binary':
                x = pd.to_numeric(df[col], errors='coerce').fillna(info['fill']).astype(np.float32).values.reshape(-1, 1)
                parts.append(x)
            elif info['type'] == 'numeric':
                x = pd.to_numeric(df[col], errors='coerce').fillna(info['fill']).values.reshape(-1, 1)
                x = info['scaler'].transform(x).astype(np.float32)
                parts.append(x)
            else:
                vals = df[col].fillna('MISSING').astype(str).str.strip().values.reshape(-1, 1)
                x    = info['ohe'].transform(vals).astype(np.float32)
                parts.append(x)
        return np.concatenate(parts, axis=1).astype(np.float32) if parts else np.zeros((len(df), 0), dtype=np.float32)

    @property
    def feature_dim(self):
        dim = 0
        for col in self.meta_cols:
            info = self.colinfo[col]
            if info['type'] == 'gender':
                dim += 1                                        # SỬA: 1 thay vì 2 hoặc 3
            elif info['type'] in ['binary', 'numeric']:
                dim += 1
            else:
                dim += len(info['ohe'].categories_[0])
        return dim
class MetadataMLP(nn.Module):
    """Encode raw metadata features -> dense embedding vector."""
    def __init__(self, input_dim, hidden_dims, embed_dim, dropout=0.1):
        super().__init__()
        dims   = [input_dim] + list(hidden_dims)
        layers = []
        for i in range(len(dims) - 1):
            layers += [nn.Linear(dims[i], dims[i+1]),
                       nn.LayerNorm(dims[i+1]), nn.GELU(), nn.Dropout(dropout)]
        layers += [nn.Linear(dims[-1], embed_dim), nn.LayerNorm(embed_dim)]
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x)


class MetadataCrossAttentionBlock(nn.Module):
    """Per-stage Cross-Attention: image features attend to metadata tokens.
    GIỮ NGUYÊN như bản cross-attention phân cấp (gating + zero-init out_proj)."""
    def __init__(self, channels, meta_dim, num_heads=4, num_tokens=4,
                 dropout=0.05, init_zero=True):
        super().__init__()
        assert channels % num_heads == 0, f'channels {channels} must be divisible by num_heads {num_heads}'
        self.channels   = channels
        self.num_tokens = num_tokens
        self.meta_to_kv  = nn.Linear(meta_dim, num_tokens * channels)
        self.meta_norm   = nn.LayerNorm(channels)
        self.cross_attn  = nn.MultiheadAttention(
            embed_dim=channels, num_heads=num_heads, dropout=dropout, batch_first=True)
        self.out_proj    = nn.Linear(channels, channels)
        self.gate_proj   = nn.Linear(meta_dim, channels)
        self.query_norm  = nn.LayerNorm(channels)
        self.dropout     = nn.Dropout(dropout)
        if init_zero:
            nn.init.zeros_(self.out_proj.weight); nn.init.zeros_(self.out_proj.bias)
            nn.init.zeros_(self.gate_proj.weight); nn.init.zeros_(self.gate_proj.bias)

    def forward(self, feat, meta_embed):
        B, C, H, W = feat.shape
        feat_flat = feat.permute(0, 2, 3, 1).reshape(B, H * W, C)
        query     = self.query_norm(feat_flat)
        kv_flat   = self.meta_to_kv(meta_embed)
        kv_tokens = self.meta_norm(kv_flat.view(B, self.num_tokens, C))
        attn_out, _ = self.cross_attn(query, kv_tokens, kv_tokens, need_weights=False)
        attn_out    = self.out_proj(attn_out)
        gate = torch.sigmoid(self.gate_proj(meta_embed)).unsqueeze(1)
        out  = feat_flat + gate * self.dropout(attn_out)
        return out.reshape(B, H, W, C).permute(0, 3, 1, 2)


class LocalHierarchyHead(nn.Module):
    """Classification head (giữ nguyên khối; flat baseline dùng 1 head)."""
    def __init__(self, in_dim, hidden_dim, out_dim, dropout=0.2):
        super().__init__()
        self.net = nn.Sequential(
            nn.LayerNorm(in_dim), nn.Linear(in_dim, hidden_dim),
            nn.GELU(), nn.Dropout(dropout), nn.Linear(hidden_dim, out_dim))

    def forward(self, x):
        return self.net(x)


class HierarchicalSwinCrossAttnLocalHeads(nn.Module):
    """FLAT baseline: GIỮ TÊN class + kiến trúc Swin + Cross-Attention metadata,
    nhưng thay 3 head phân cấp bằng 1 flat_head dự đoán 10 lớp (no-tumor + 9 leaf).
    flat_head ăn từ [s1,s2,s3] — đúng concat đầu vào của leaf_head bản phân cấp,
    để so sánh tầng leaf công bằng (cùng feature, cùng dung lượng head)."""
    def __init__(self, meta_dim, use_metadata=True):
        super().__init__()
        self.use_metadata = use_metadata
        self.backbone = timm.create_model(
            CFG.model_name, pretrained=CFG.pretrained,
            features_only=True, out_indices=(0, 1, 2, 3), img_size=CFG.img_size)
        self.stage_channels = list(self.backbone.feature_info.channels())
        c0, c1, c2, c3 = self.stage_channels

        if self.use_metadata:
            self.meta_encoder = MetadataMLP(
                meta_dim, CFG.meta_hidden_dims, CFG.meta_embed_dim, CFG.meta_dropout)
            self.ca_blocks = nn.ModuleList([
                MetadataCrossAttentionBlock(
                    channels=c, meta_dim=CFG.meta_embed_dim,
                    num_heads=CFG.ca_num_heads, num_tokens=CFG.ca_num_tokens,
                    dropout=CFG.ca_dropout, init_zero=True)
                for c in self.stage_channels])
        else:
            self.meta_encoder = None
            self.ca_blocks    = None

        # ── 1 HEAD phẳng: 10 lớp (no-tumor + 9 leaf), input [s1,s2,s3] ──
        self.flat_head = LocalHierarchyHead(c1 + c2 + c3, CFG.head_hidden_dim,
                                            NUM_FLAT, CFG.classifier_dropout)

        # ── ECL: projection head contrastive — ăn từ feature ẢNH THUẦN (trước cross-attn).
        # LayerNorm sau mỗi Linear: ổn định scale -> F.normalize không nổ gradient (an toàn AMP).
        self.use_ecl = getattr(CFG, 'use_ecl', False)
        if self.use_ecl:
            # Projection head: Linear -> LayerNorm -> ReLU -> Linear -> LayerNorm.
            # Tác giả (ecl.py self.head) dùng BatchNorm1d, nhưng ta đổi sang LayerNorm vì:
            #  (1) an toàn với batch nhỏ (BatchNorm1d crash khi batch=1);
            #  (2) DataParallel-safe (không lệch running stats giữa 2 GPU);
            #  (3) LayerNorm cuối chống F.normalize nổ gradient dưới AMP (vector gần-zero).
            # Tác giả không gặp các vấn đề này vì chạy fp32 + drop_last + 1 GPU.
            self.contrastive_proj_head = nn.Sequential(
                nn.Linear(c1 + c2 + c3, CFG.ecl_proj_hidden),
                nn.LayerNorm(CFG.ecl_proj_hidden),    # LayerNorm thay BatchNorm1d (an toàn batch nhỏ + DataParallel)
                nn.ReLU(inplace=True),
                nn.Linear(CFG.ecl_proj_hidden, CFG.ecl_embed_dim),
                nn.LayerNorm(CFG.ecl_embed_dim),      # bổ sung thêm (AMP safety, không có ở gốc)
            )
        else:
            self.contrastive_proj_head = None

    def forward_features(self, images, metadata):
        feats      = self.backbone(images)
        meta_embed = self.meta_encoder(metadata) if (self.use_metadata and
                                                     self.meta_encoder is not None) else None
        pooled     = []   # ĐÃ fusion metadata (cho classification)
        pooled_img = []   # ẢNH THUẦN, chưa fusion metadata (cho contrastive ECL)
        for i, feat in enumerate(feats):
            if feat.ndim == 4 and feat.shape[-1] == self.stage_channels[i]:
                feat = feat.permute(0, 3, 1, 2).contiguous()
            assert feat.shape[1] == self.stage_channels[i], f'Unexpected feature layout: {feat.shape}'
            pooled_img.append(feat.mean(dim=(2, 3)))     # pool TRƯỚC cross-attention
            if self.use_metadata and self.ca_blocks is not None and meta_embed is not None:
                feat = self.ca_blocks[i](feat, meta_embed)
            pooled.append(feat.mean(dim=(2, 3)))
        return pooled, pooled_img, meta_embed

    def forward(self, images, metadata):
        pooled, pooled_img, _ = self.forward_features(images, metadata)
        s0, s1, s2, s3 = pooled
        out = {'flat': self.flat_head(torch.cat([s1, s2, s3], dim=1))}
        # ── ECL: z_contrastive từ feature ẢNH THUẦN (TÁCH metadata) ──
        if self.use_ecl and self.contrastive_proj_head is not None:
            si1, si2, si3 = pooled_img[1], pooled_img[2], pooled_img[3]
            embed_img = torch.cat([si1, si2, si3], dim=1)   # cùng dim với embed
            z = self.contrastive_proj_head(embed_img)
            out['z_contrastive'] = F.normalize(z, dim=-1)   # (B, ecl_embed_dim)
        return out

    def freeze_backbone(self, freeze=True):
        for p in self.backbone.parameters():
            p.requires_grad = not freeze

    def get_param_groups(self, lr, backbone_lr_scale=0.1, meta_lr_scale=1.0):
        head_params = list(self.flat_head.parameters())
        if self.contrastive_proj_head is not None:
            head_params += list(self.contrastive_proj_head.parameters())   # ECL proj head
        groups = [
            {'params': self.backbone.parameters(),
             'lr': lr * backbone_lr_scale, 'name': 'backbone'},
            {'params': head_params, 'lr': lr, 'name': 'heads'},
        ]
        meta_params = []
        if self.meta_encoder is not None: meta_params += list(self.meta_encoder.parameters())
        if self.ca_blocks is not None:    meta_params += list(self.ca_blocks.parameters())
        if meta_params:
            groups.append({'params': meta_params, 'lr': lr * meta_lr_scale, 'name': 'metadata_ca'})
        return groups
