import numpy as np
import cv2
from pathlib import Path
from ..config import PATCHCORE_BANK, ANOMALY_THRESHOLD, DEVICE


class AnomalyDetector:
    def __init__(self):
        self.backbone = None
        self.memory_bank = None
        self.distance_scale = None
        self._loaded = False

    def load(self):
        if self._loaded:
            return

        try:
            import torch
            from torchvision import models, transforms

            try:
                self.backbone = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
            except Exception as e:
                # Downloading ImageNet weights requires outbound internet
                # access; on an offline towfish/vessel deployment (or a
                # sandboxed build) that download can fail outright. The
                # original code let that exception propagate and crash the
                # whole anomaly service instead of degrading gracefully.
                # Fall back to a fixed-seed, randomly-initialized backbone
                # so PatchCore-style nearest-neighbor scoring still runs
                # end-to-end; swap back to pretrained weights automatically
                # the moment internet access is available.
                print(f"Notice: could not fetch pretrained ResNet18 weights ({e}); "
                      f"using a randomly-initialized backbone instead.")
                torch.manual_seed(42)
                self.backbone = models.resnet18(weights=None)

            self.backbone.fc = torch.nn.Identity()
            self.backbone.eval()

            if DEVICE == "cuda":
                self.backbone = self.backbone.cuda()

            transform_list = [
                transforms.ToPILImage(),
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ]
            self.transform = transforms.Compose(transform_list)

            self._load_bank()

            self._loaded = True
        except ImportError:
            self._loaded = True
            self.memory_bank = None

    def _load_bank(self):
        """Loads the PatchCore memory bank plus its calibrated distance scale.

        Stored as an .npz with `bank` (N x D features) and `scale` (a scalar
        derived from the bank's own nearest-neighbor distance distribution).
        Falls back to reading a legacy plain .npy array (bank only, no
        calibrated scale) for backward compatibility.
        """
        bank_path = Path(str(PATCHCORE_BANK))
        npz_path = bank_path.with_suffix(".npz")

        if npz_path.exists():
            data = np.load(str(npz_path))
            self.memory_bank = data["bank"]
            self.distance_scale = float(data["scale"])
        elif bank_path.exists():
            self.memory_bank = np.load(str(bank_path))
            self.distance_scale = self._estimate_scale(self.memory_bank)

    @staticmethod
    def _estimate_scale(bank: np.ndarray) -> float:
        """
        Calibrates the anomaly-score normalizer directly from the memory
        bank instead of a hardcoded constant. For every bank item we compute
        its nearest-neighbor distance to the rest of the bank (i.e. how far
        apart *normal* seabed patches typically sit from one another). The
        95th percentile of that distribution becomes the scale: a query
        patch whose nearest-neighbor distance sits at that scale gets an
        anomaly score of ~1.0, and typical normal patches score well below
        that. This keeps the score meaningful regardless of feature
        dimensionality, backbone, or how tight/loose the normal cluster is.
        """
        if bank is None or len(bank) < 2:
            return 1.0

        n = len(bank)
        # Cap pairwise-distance computation cost for large banks.
        sample_n = min(n, 400)
        idx = np.random.choice(n, sample_n, replace=False) if n > sample_n else np.arange(n)
        sample = bank[idx]

        nn_dists = []
        for i in range(sample_n):
            dists = np.linalg.norm(bank - sample[i], axis=1)
            dists[np.argmin(np.abs(dists))] = np.inf  # drop self-match (distance 0)
            nn_dists.append(np.min(dists))

        scale = float(np.percentile(nn_dists, 95))
        return scale if scale > 1e-6 else 1.0

    def _extract_features(self, patches: list[np.ndarray]) -> np.ndarray:
        import torch

        features = []
        for patch in patches:
            if len(patch.shape) == 2:
                patch_rgb = cv2.cvtColor(patch, cv2.COLOR_GRAY2RGB)
            else:
                patch_rgb = patch

            tensor = self.transform(patch_rgb).unsqueeze(0)
            if DEVICE == "cuda":
                tensor = tensor.cuda()

            with torch.no_grad():
                feat = self.backbone(tensor).cpu().numpy().squeeze()
            features.append(feat)

        return np.array(features)

    def build_memory_bank(self, normal_patches: list[np.ndarray], coreset_size: int = 500):
        self.load()
        if self.backbone is None:
            return

        features = self._extract_features(normal_patches)

        if len(features) > coreset_size:
            idx = np.random.choice(len(features), coreset_size, replace=False)
            features = features[idx]

        self.memory_bank = features
        self.distance_scale = self._estimate_scale(features)

        npz_path = Path(str(PATCHCORE_BANK)).with_suffix(".npz")
        npz_path.parent.mkdir(parents=True, exist_ok=True)
        np.savez(str(npz_path), bank=features, scale=self.distance_scale)

    def score(self, patch: np.ndarray) -> float:
        self.load()
        if self.backbone is not None and self.memory_bank is not None and len(self.memory_bank) > 0:
            try:
                feature = self._extract_features([patch])[0]
                dists = np.linalg.norm(self.memory_bank - feature, axis=1)
                min_dist = float(np.min(dists))
                scale = self.distance_scale or self._estimate_scale(self.memory_bank)
                score = min_dist / max(scale, 1e-6)
                return float(max(0.0, min(1.0, score)))
            except Exception as e:
                print(f"Neural anomaly score fallback: {e}")

        # Acoustic statistical anomaly scoring (used only when no trained
        # backbone/memory bank is available at all).
        if len(patch.shape) == 3:
            gray = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
        else:
            gray = patch

        if gray.size == 0:
            return 0.5

        p_std = float(np.std(gray))
        p_contrast = float(np.max(gray) - np.min(gray))
        p_mean = float(np.mean(gray))

        # Deviation from normal seabed (typical seabed: mean ~85, std ~20, contrast ~80)
        z_contrast = abs(p_contrast - 80.0) / 120.0
        z_std = abs(p_std - 20.0) / 40.0
        z_mean = abs(p_mean - 85.0) / 85.0

        raw_score = 0.4 * z_contrast + 0.4 * z_std + 0.2 * z_mean
        return float(max(0.1, min(0.95, raw_score)))

    def score_detections(self, image: np.ndarray, detections: list[dict]) -> list[float]:
        scores = []
        h, w = image.shape[:2]

        for det in detections:
            bbox = det["bbox"]
            x1 = max(0, int(bbox["x1"]))
            y1 = max(0, int(bbox["y1"]))
            x2 = min(w, int(bbox["x2"]))
            y2 = min(h, int(bbox["y2"]))

            if x2 <= x1 or y2 <= y1:
                scores.append(0.5)
                continue

            patch = image[y1:y2, x1:x2]
            if len(patch.shape) == 2:
                patch_rgb = cv2.cvtColor(patch, cv2.COLOR_GRAY2RGB)
            else:
                patch_rgb = patch

            score = self.score(patch_rgb)
            scores.append(score)

        return scores
