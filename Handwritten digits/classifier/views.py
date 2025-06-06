from django.shortcuts import render

# Create your views here.
import cv2
import numpy as np
import torch
from torchvision import transforms
from PIL import Image

from rest_framework.views import APIView
from rest_framework.response import Response

from .serializers import ImageUploadSerializer
from .model_resnet import ResNetDigit

class PredictDigit(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.device = torch.device("cpu")
        # Load your trained weights here:
        self.model = ResNetDigit(pretrained=False).to(self.device)
        self.model.load_state_dict(torch.load(
            "classifier/resnet_digit.pt", map_location=self.device
        ))
        self.model.eval()
        # Preprocess transforms for 28×28 crops
        self.tfms = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.5,), (0.5,))
        ])

    def post(self, request):
        serializer = ImageUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        # 1) Read and convert to grayscale array
        img = serializer.validated_data['image']
        pil = Image.open(img).convert("L")
        img_np = np.array(pil)

        # 2) Binarize & denoise
        _, bw = cv2.threshold(img_np, 128, 255, cv2.THRESH_BINARY_INV)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
        clean = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, kernel, iterations=1)

        # 3) Connected components for digit regions
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(clean, 8)
        regions = []
        for i in range(1, num_labels):
            x, y, w, h, area = stats[i]
            if area < 50:  # noise filter
                continue
            crop = clean[y:y+h, x:x+w]
            resized = cv2.resize(crop, (28, 28))
            regions.append((x, resized))

        if not regions:
            return Response({'prediction': ''})

        # 4) Sort & batch inference
        regions.sort(key=lambda r: r[0])
        tensors = [self.tfms(Image.fromarray(r)) for _, r in regions]
        batch = torch.stack(tensors).to(self.device)
        with torch.no_grad():
            outputs = self.model(batch)
            preds = outputs.argmax(dim=1).cpu().tolist()

        # 5) Return joined prediction
        digit_string = ''.join(str(p) for p in preds)
        return Response({'prediction': digit_string})

