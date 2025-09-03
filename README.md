# Development Setup with Docker Compose

This project provides a ready-to-use **development environment** with Docker and Docker Compose.  
It runs the application along with its dependencies in containers.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed  
- [Docker Compose](https://docs.docker.com/compose/install/) installed  

## Getting Started

1. Copy the environment example file and adjust values as needed:

   ```bash
   cp .env.example .env

2. Build and start the services:

    ```bash
    docker-compose up --build
3. Access the application:

- API: http://localhost:8000
- API docs: http://localhost:8000/docs


# Documentation

1. Databases

## General code submission info (PostgreSQL)

- **Examples:** `user_id`, `submission_id`, `timestamp`, `programming_language`, `status` (success/failure).  
- **Nature of data:** Structured, predictable, and benefits from relations (e.g., linking to a `users` table).  
- **Query use cases:**  
  - “Show me all successful submissions per user in the last 24h.”  
  - “Aggregate average runtime per language.”  
- **Why PostgreSQL?** Because submissions are **structured, relational, and query-heavy**.

---

## AI service response (MongoDB)

- **Examples:** Raw AI output, explanations, logs, error messages, structured/unstructured JSON responses.  
- **Nature of data:** Can vary widely (sometimes plain text, sometimes JSON, sometimes multiple nested fields).  
- **Schema flexibility:** You don’t want to force a rigid schema → flexibility matters.  
- **Why MongoDB?** Because AI outputs are **unstructured, variable, and better stored as documents**.  
  MongoDB makes it easy to just dump and query JSON-like objects without rigid schemas.