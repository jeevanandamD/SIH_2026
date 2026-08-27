import numpy as np
import cv2
from pathlib import Path
from ..config import PATCHCORE_BANK, ANOMALY_THRESHOLD, DEVICE


class AnomalyDetector:
    def __init__(self):
        self.backbone = None
        self.memory_bank = None
        self._loaded = False

    def load(self):
        if self._loaded:
            return

        try:
            import torch
            from torchvision import models, transforms

            self.backbone = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
            self.backbone.fc = __import__("torch").nn.Identity()
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

            if PATCHCORE_BANK.exists():
                self.memory_bank = np.load(str(PATCHCORE_BANK))

            self._loaded = True
        except ImportError:
            self._loaded = True
            self.memory_bank = None

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
        np.save(str(PATCHCORE_BANK), features)

    def score(self, patch: np.ndarray) -> float:
        self.load()
        if self.backbone is not None and self.memory_bank is not None:
            try:
                feature = self._extract_features([patch])[0]
                dists = np.linalg.norm(self.memory_bank - feature, axis=1)
                min_dist = float(np.min(dists))
                max_possible = 100.0
                score = min(min_dist / max_possible, 1.0)
                return max(0.0, min(1.0, score))
            except Exception as e:
                print(f"Neural anomaly score fallback: {e}")

        # Acoustic statistical anomaly scoring
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
