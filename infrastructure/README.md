# CALDIM IntelliSolve AI — Infrastructure Setup Guide

This directory contains configuration templates and guidance for running supporting infrastructure services (such as PostgreSQL and Ollama).

## Workstation Environment Analysis

During Phase 1 inspection, the following local services were detected:
- **PostgreSQL 18.6**: Installed natively on Windows (`C:\Program Files\PostgreSQL\18\bin\psql.exe`) with the `postgresql-x64-18` Windows service installed and running.
- **Docker Desktop**: Docker 29.6.2 CLI is present, but `com.docker.service` is currently stopped.

Because PostgreSQL is already running natively as a Windows service, **Docker is not required** for Phase 1 or Phase 2 local development.

---

## Option A: Native Windows Services (Recommended for this machine)

### 1. PostgreSQL 18 Native Service
- Verify the service status in PowerShell:
  ```powershell
  Get-Service postgresql*
  ```
- To start the service if stopped:
  ```powershell
  Start-Service postgresql-x64-18
  ```
- When ready for Phase 2 database creation:
  ```powershell
  & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -c "CREATE DATABASE caldim_intellisolve;"
  ```

---

## Option B: Optional Docker Compose (Alternative)

If you prefer to run PostgreSQL in an isolated Docker container instead of the native Windows service:
1. Start Docker Desktop:
   ```powershell
   Start-Service com.docker.service
   ```
2. Copy the example compose file:
   ```powershell
   Copy-Item infrastructure/docker-compose.example.yml docker-compose.yml
   ```
3. Start the container:
   ```powershell
   docker compose up -d
   ```
