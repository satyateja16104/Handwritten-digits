
import time
import torch
from torch import nn, optim
from torch.optim.lr_scheduler import CosineAnnealingLR
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
from sklearn.metrics import confusion_matrix
from classifier.model_resnet import ResNetDigit

def main():
    device = torch.device("cpu")
    print(f"Training on {device}\n")

    # 1) Data transforms: all PIL-based ops FIRST, then ToTensor + Normalize,
    #    then RandomErasing (which operates on Tensors).
    train_tfms = transforms.Compose([
        transforms.RandomAffine(
            degrees=15,
            translate=(0.1, 0.1),
            shear=10,
            scale=(0.9, 1.1)
        ),
        transforms.RandomPerspective(distortion_scale=0.3, p=0.5),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
        transforms.Normalize((0.5,), (0.5,)),
        transforms.RandomErasing(p=0.3, scale=(0.02, 0.1)),  # NOW works on Tensor
    ])
    val_tfms = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.5,), (0.5,)),
    ])

    # 2) Datasets & loaders
    train_ds = datasets.MNIST('data/', train=True, download=True, transform=train_tfms)
    val_ds   = datasets.MNIST('data/', train=False, download=True, transform=val_tfms)
    train_loader = DataLoader(train_ds, batch_size=64, shuffle=True,  num_workers=0)
    val_loader   = DataLoader(val_ds,   batch_size=128, shuffle=False, num_workers=0)

    # 3) Model, criterion, optimizer, scheduler
    model = ResNetDigit(pretrained=False).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)
    num_epochs = 20
    scheduler = CosineAnnealingLR(optimizer, T_max=num_epochs, eta_min=1e-5)

    best_val_acc = 0.0
    wait = 0

    for epoch in range(1, num_epochs + 1):
        t0 = time.time()

        # — Train —
        model.train()
        train_loss = 0.0
        for imgs, labels in train_loader:
            imgs, labels = imgs.to(device), labels.to(device)
            with torch.amp.autocast(device_type="cpu"):
                outputs = model(imgs)
                loss = criterion(outputs, labels)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * imgs.size(0)
        train_loss /= len(train_loader.dataset)

        # — Validate —
        model.eval()
        correct = 0
        all_preds, all_labels = [], []
        with torch.no_grad():
            for imgs, labels in val_loader:
                imgs, labels = imgs.to(device), labels.to(device)
                outputs = model(imgs)
                preds = outputs.argmax(dim=1)
                correct += (preds == labels).sum().item()
                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())

        val_acc = correct / len(val_loader.dataset)

        # — Confusion matrix & recall —
        cm = confusion_matrix(all_labels, all_preds)
        recall = cm.diagonal() / cm.sum(axis=1)

        epoch_time = time.time() - t0
        print(f"\nEpoch {epoch}/{num_epochs} — {epoch_time:.1f}s")
        print(f"  Train Loss: {train_loss:.4f} | Val Acc: {val_acc:.4%}")
        print("  Confusion Matrix:")
        for row in cm:
            print("   ", row)
        for i, r in enumerate(recall):
            print(f"    Class {i} recall: {r:.3f}")

        # — Save best & early-stop —
        if val_acc > best_val_acc + 1e-4:
            best_val_acc = val_acc
            wait = 0
            torch.save(model.state_dict(), "classifier/resnet_digit.pt")
            
        else:
            wait += 1
            print(f"  No improvement ({wait}/5)")

        if wait >= 5:
            print("⏹ Early stopping")
            break

        scheduler.step()

    print(f"\n Done. Best Val Acc: {best_val_acc:.4%}")

if __name__ == "__main__":
    main()
