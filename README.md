# Cheque Processing System

A full-stack cheque processing application that extracts cheque information using OCR and validates transactions against a customer's available balance.

## Features

- Upload multiple cheque images
- Detect duplicate cheque uploads
- OCR-based handwritten amount extraction
- Automatic balance validation
- Accept or reject cheques based on available balance
- Processing history tracking
- PDF report generation
- React frontend dashboard
- Django REST API backend

---

## Architecture

Frontend:
- React
- Tailwind CSS

Backend:
- Django
- Django REST Framework

OCR:
- Microsoft TrOCR
- OpenCV

Reporting:
- ReportLab PDF Generator

---

## Workflow

1. User enters:
   - Customer Name
   - Initial Balance

2. User uploads cheque images

3. System:
   - Detects duplicates
   - Extracts cheque amount using OCR
   - Validates against remaining balance

4. Result:
   - Accepted Cheque
   - Rejected Cheque

5. PDF report can be generated

---

## Project Structure

```
project-root/
│
├── frontend/
│   ├── src/
│   └── public/
│
├── backend/
│   ├── cheques/
│   ├── templates/
│   └── manage.py
│
└── README.md
```

---

## OCR Pipeline

1. Upload cheque image
2. OpenCV preprocessing
3. Amount region localization
4. TrOCR text extraction
5. Numeric amount parsing
6. Balance validation

---

## Technologies Used

| Category | Technology |
|-----------|------------|
| Frontend | React |
| Styling | Tailwind CSS |
| Backend | Django |
| API | Django REST Framework |
| OCR | TrOCR |
| Image Processing | OpenCV |
| PDF Reports | ReportLab |
| Database | SQLite |

---

## Installation

### Backend

```bash
cd backend

python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt

python manage.py migrate

python manage.py runserver 9001
```

### Frontend

```bash
cd frontend

npm install

npm run dev
```

---

## API Endpoint

### Process Cheques

```http
POST /api/cheques/
```

Form Data:

```text
customer_name
balance
cheques[]
```

---

## Sample Response

```json
{
  "session_id": 1,
  "customer_name": "John",
  "initial_balance": 50000,
  "remaining_balance": 27500,
  "cheques": [
    {
      "image_name": "cheque1.jpg",
      "amount": 22500,
      "status": "accepted"
    }
  ]
}
```

---

## Future Enhancements

### YOLO-based Field Detection

Current implementation uses OpenCV template matching and ROI extraction.

Future versions can use YOLO object detection to automatically identify:

- Amount Field
- Date Field
- Signature Area

Benefits:

- Supports multiple bank layouts
- Better accuracy
- Reduced manual ROI tuning
- Easier scalability

---

## Screenshots

### Upload Screen

(Add screenshot here)

### Processing Results

(Add screenshot here)

### PDF Report

(Add screenshot here)

---

## Learning Outcomes

This project demonstrates:

- Computer Vision
- OCR Pipelines
- Django REST APIs
- React Frontend Development
- Image Processing using OpenCV
- Document Processing Systems
- PDF Generation
- Full Stack Development

---

## Author

Satyateja Y
