# AI-Powered Customer Support System

A comprehensive customer support system that leverages AI to provide efficient and automated support solutions.

## System Architecture

### Key Components

1. **Frontend (React + TypeScript)**
   - User Interface for customers and admins
   - Real-time chat and support ticket management
   - Interactive dashboard for admins
   - Multi-media support (text, voice, image, screen share)

2. **Backend (Node.js + Express + TypeScript)**
   - RESTful API endpoints
   - WebSocket for real-time communication
   - Integration with AI services
   - Database management

3. **AI Agents**
   - Summarization Agent
   - Action Extraction Agent
   - Task Routing Agent
   - Resolution Recommendation Agent
   - Resolution Time Estimation Agent
   - Proactive Prevention Agent

### Features

- **User Features**
  - Multi-channel support (text, voice, image, screen share)
  - Real-time AI assistance
  - Proactive issue prevention
  - Status tracking and updates

- **Admin Features**
  - Comprehensive dashboard
  - Ticket management
  - AI performance monitoring
  - Knowledge base management

- **AI Features**
  - Natural language processing
  - Computer vision for image analysis
  - Predictive analytics
  - Automated routing and resolution

## Setup Instructions

### Prerequisites
- Node.js (v16 or higher)
- npm
- Python 3.8+ (for AI services)
- SQL lite (for database)

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   # Frontend
   cd frontend
   npm install

   # Backend
   cd ../backend
   npm install
   ```

3. Set up environment variables:
   - Create `.env` files in both frontend and backend directories
   - Configure necessary API keys and database connections

4. Start the development servers:
   ```bash
   # Frontend
   cd frontend
   npm run dev

   # Backend
   cd venv/scripts
   activate
   cd ../../backend
   uvicorn main:app --reload
   

   # Admin Panel
   cd frontend
   npm run dev:admin
   ```

## Development

### Project Structure

```
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API services
│   │   ├── hooks/         # Custom hooks
│   │   └── utils/         # Utility functions
│   └── public/            # Static assets
│
├── backend/
│   ├── src/
│   │   ├── controllers/   # Route controllers
│   │   ├── models/        # Database models
│   │   ├── services/      # Business logic
│   │   ├── routes/        # API routes
│   │   └── utils/         # Utility functions
│   └── config/            # Configuration files
```

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE.md file for details"# Customer_Support_AI_AGENTs" 
