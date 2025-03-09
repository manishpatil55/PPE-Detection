# PPE Detection & Alert System

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat)](https://streamlit.io)
[![YOLOv11](https://img.shields.io/badge/YOLOv11-00FF00?style=flat)](https://ultralytics.com)
[![Twilio](https://img.shields.io/badge/Twilio-F22F46?style=flat)](https://twilio.com)

Real-time personal protective equipment detection with instant safety alerts.

## Key Features

- Real-time PPE detection using YOLOv11
- Site-specific safety requirements
- Instant SMS/Email alerts
- Web interface with live camera feed
- Configurable for any workplace

## Quick Start

1. **Clone Repository**
```bash
git clone https://github.com/yourusername/ppe-detection-system.git
cd ppe-detection-system
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure Settings**  
Create `.env` file:
```ini
TWILIO_SID=your_account_sid
TWILIO_TOKEN=your_auth_token
TWILIO_PHONE=your_teilio_phone_number
```

4. **Run Application**
```bash
streamlit run app.py
```

## Configuration

Define workspaces in `sites.yaml`:
```yaml
construction_site:
  required_ppe: ["Helmet", "Vest"]
  contacts:
    sms: "+1234567890"

chemical_lab:
  required_ppe: ["Gloves", "Mask", "Glasses"]
  contacts: 
    sms: "+0987654321"
```

## How It Works

1. Camera captures live video feed
2. AI model detects PPE items
3. System checks against site requirements
4. Alerts sent if missing equipment
5. Dashboard shows real-time status

## Contributing

We welcome improvements! Please:
1. Fork the repository
2. Create your feature branch
3. Submit a pull request

## License

MIT License - [LICENSE](LICENSE)
