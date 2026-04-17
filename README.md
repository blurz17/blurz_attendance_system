# Blurz Attendance System

A comprehensive End-to-End Attendance System built with a modern tech stack. The system is split into a central backend API, an admin frontend, and a client (student/instructor) frontend.

## Features
- **User Management**: Admin dashboard to manage students, instructors, and system settings.
- **Attendance Tracking**: Real-time attendance monitoring and record keeping.
- **Client App**: Interface for users to check in, view their attendance history, and engage with quizzes/courses.
- **Background Tasks**: Celery and Redis integrated for asynchronous task processing.

## Technologies Used
- **Backend**: FastAPI, PostgreSQL, Alembic, Celery, Redis.
- **Frontend (Admin)**: React, Vite, TypeScript, Tailwind CSS.
- **Frontend (Client)**: React, Vite, TypeScript, Tailwind CSS.
- **Testing**: Pytest setup for backend End-to-End verification.

## Prerequisites
- Node.js (v18+)
- Python (3.10+)
- PostgreSQL configured and running
- Redis Server (for Celery tasks)

## Getting Started

### 1. Database Setup
Ensure PostgreSQL and Redis are running locally.
You will need to create a `.env` file in the `server` directory and configure the database connection, JWT secret keys, etc. Add required environment variables similar to `.env.example` (if provided).

### 2. Backend Server Setup
1. Open a terminal and navigate to the `server` directory:
   ```bash
   cd server
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run database migrations:
   ```bash
   alembic upgrade head
   ```
5. Start the backend server:
   ```bash
   uvicorn main:app --reload
   ```

*(Optional)* Run Celery worker for background tasks (using `gevent` or `solo` pool on Windows):
```bash
celery -A core.services.celery.celery_tasks worker --loglevel=info -P gevent
```

### 3. Admin Frontend Setup
1. Open a new terminal and navigate to the admin portal directory:
   ```bash
   cd web_version/admin
   ```
2. Install Node modules:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```

### 4. Client Frontend Setup
1. Open a new terminal and navigate to the client application directory:
   ```bash
   cd web_version/client
   ```
2. Install Node modules:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
