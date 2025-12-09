# HuskyHub 🐾

A peer-to-peer service marketplace for Northeastern University students. Students can offer and request services like tutoring, moving help, photography, and more within the trusted Northeastern community.

## Tech Stack

- **Database:** MySQL 9.0
- **Backend:** Flask (Python)
- **Frontend:** Streamlit
- **Containerization:** Docker

## Getting Started

### 1. Clone the Repository

```bash
git clone <repository-url>
cd HUSKYHUB_CS3200
```

### 2. Create the Environment File

Create a file named `.env` inside the `api/` folder with the following contents:

```env
SECRET_KEY=your_secret_key_here
DB_USER=root
DB_HOST=db
DB_PORT=3306
DB_NAME=HuskyHub
MYSQL_ROOT_PASSWORD=huskyhub_password123
```

### 3. Start the Application

```bash
docker compose up -d
```

This will:
- Start the MySQL database and execute all SQL files
- Start the Flask API server
- Start the Streamlit frontend

### 4. Access the Application

| Service | URL |
|---------|-----|
| Streamlit App | http://localhost:8501 |
| Flask API | http://localhost:4000 |
| MySQL Database | localhost:3200 |

### Stopping the Application

```bash
docker compose down
```

To reset the database completely:

```bash
docker compose down -v
docker compose up -d
```

## Team Members

- Lydia O'Neill
- Andrew Kwon
- Alex Zheng
- Arshia Verma

## youtube link for the DEMO pitch video 
- https://www.youtube.com/watch?v=sYDxxFUUi8w 


---

**CS3200 Database Design** — Northeastern University