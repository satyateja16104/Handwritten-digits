import torch.nn as nn
import torchvision.models as models
import torch as torch

class ResNetDigit(nn.Module):
    def __init__(self, pretrained=True):
        super().__init__()
        # Load ResNet-18
        self.backbone = models.resnet18(pretrained=pretrained)
        # Adapt first conv to grayscale input (1 channel)
        w = self.backbone.conv1.weight
        self.backbone.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3, bias=False)
        with torch.no_grad():
            self.backbone.conv1.weight[:] = w.mean(dim=1, keepdim=True)
        # Replace final layer for 10 classes
        self.backbone.fc = nn.Linear(self.backbone.fc.in_features, 10)

    def forward(self, x):
        return self.backbone(x)
