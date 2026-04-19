# ChoreTracker

A modern family chore management application that helps families track and reward completed chores. Built with a Flask REST API backend and Vue.js frontend.

## Features

- 👨‍👩‍👧‍👦 **Family Management**: Add and manage family members
- ✅ **Chore Tracking**: Create and assign chores with monetary rewards
- 💰 **Earnings Dashboard**: Track individual earnings and payout history
- 🔐 **Admin Panel**: Manage users, chores, and system settings
- 📱 **Responsive Design**: Works on desktop and mobile devices
- 🐳 **Docker Ready**: Easy deployment with Docker Compose

## Tech Stack

### Backend
- **Flask** - Python web framework
- **SQLAlchemy** - ORM for database operations
- **PostgreSQL** - Primary database
- **Flask-CORS** - Cross-origin resource sharing
- **Flask-Mail** - Email functionality

### Frontend
- **Vue.js 3** - Progressive JavaScript framework
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **Vue Router** - Official router for Vue.js
- **Pinia** - State management
- **Axios** - HTTP client

### DevOps
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **Nginx** - Web server for production

## Prerequisites

- Docker and Docker Compose
- Node.js 20+ (for local frontend development)
- Python 3.11+ (for local backend development)

## Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/fordChores.git
   cd fordChores
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the application**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Frontend: http://localhost:8080
   - Backend API: http://localhost:5001

## Local Development Setup

### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd chores
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r ../requirements.txt
   ```

4. **Set environment variables**
   ```bash
   export DATABASE_URL="sqlite:///instance/chores.db"
   export SECRET_KEY="your-secret-key"
   ```

5. **Run the backend**
   ```bash
   flask run
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

## API Documentation

The REST API provides endpoints for:

- **Users**: `/api/v1/users/`
  - GET: List all users
  - POST: Add new user
  - PUT: Update user
  - DELETE: Remove user

- **Chores**: `/api/v1/chores/`
  - GET: List all chores
  - POST: Create new chore
  - PUT: Update chore
  - DELETE: Remove chore
  - POST: `/api/v1/chores/complete` - Mark chore as completed

- **User Balance**: `/api/v1/users/{id}/balance`
- **User History**: `/api/v1/users/{id}/history`

## Project Structure

```
fordChores/
├── chores/                 # Flask backend
│   ├── models/            # SQLAlchemy models
│   ├── routes/            # API route handlers
│   ├── database/          # Database setup and utilities
│   ├── extension/         # Flask extensions (mail, etc.)
│   └── __init__.py        # App factory
├── frontend/              # Vue.js frontend
│   ├── src/
│   │   ├── components/    # Vue components
│   │   ├── views/         # Page components
│   │   ├── stores/        # Pinia stores
│   │   └── router/        # Vue Router config
│   └── public/            # Static assets
├── instance/              # Instance-specific data (database)
├── docker-compose.yaml    # Docker orchestration
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Environment Variables

Create a `.env` file in the root directory:

```env
# Database
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=chores_db

# Flask
SECRET_KEY=your-secret-key

# Email (optional)
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com

# External APIs (optional)
ALLOWED_ORIGINS=http://localhost:8080,http://localhost:3000
VITE_API_URL=http://localhost:5001/api/v1

# Pocket Money integration (optional)
PM_BASE_URL=https://api.pocketmoney.com
PM_LOOKUP_PATH=/api/lookup
PM_DEPOSIT_PATH=/api/deposit
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Testing

### Backend Tests
```bash
cd chores
python -m pytest
```

### Frontend Tests
```bash
cd frontend
npm run test:unit
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Version

Current version: 1.1.0</content>
<parameter name="filePath">/Users/alanford/Documents/GitHub/fordChores/README.md
