# Project Report: Cloud-Based Complaint Management System

## 1. Introduction
The Cloud-Based Complaint Management System (CMS) is a modern web application designed to streamline the process of submitting, tracking, and resolving complaints. Leveraging cloud computing principles, the system ensures high availability, scalability, and security.

## 2. Problem Statement
Traditional complaint systems often suffer from lack of transparency, manual tracking errors, and limited accessibility. This project aims to digitize the lifecycle of a complaint from submission to resolution.

## 3. Existing System
Manual or legacy systems often lack:
- Real-time status tracking.
- Secure, role-based access.
- Cloud-based storage for evidence files.
- Scalable database architecture.

## 4. Proposed System
The proposed system uses a microservices-style architecture with:
- **FastAPI** for high-performance backend logic.
- **MongoDB Atlas** for a scalable, cloud-hosted NoSQL database.
- **Vanilla Frontend** for light-weight and responsive user interactions.
- **Role-Based Access Control (RBAC)** to distinguish between Users and Admins.

## 5. Cloud Service Model Used
- **PaaS (Platform as a Service):** Backend hosted on Render/AWS.
- **DBaaS (Database as a Service):** MongoDB Atlas manages all cloud data.
- **IaaS/Object Storage:** Integrated via cloud URLs for evidence management.

## 6. Deployment Model Used
- **Public Cloud:** The application is designed to be deployed on public cloud providers like AWS or Google Cloud Platform, utilizing their global infrastructure for low latency and high availability.

## 7. System Architecture
```
User → Web Browser (Frontend)
          ↓
     Cloud Hosted App (PaaS - FastAPI)
          ↓
     Cloud Database (DBaaS - MongoDB Atlas)
```

## 8. Database Design
### Users (Collection)
- `_id`: Unique Identifier
- `name`: String
- `email`: String (Unique)
- `hashed_password`: String
- `role`: Enum (user/admin)

### Complaints (Collection)
- `_id`: Unique Identifier
- `user_id`: Reference to User
- `title`: String
- `description`: Text
- `category`: String
- `status`: Enum (Pending/In Progress/Resolved)
- `admin_remarks`: Text
- `file_url`: String (Cloud evidence link)

## 9. Implementation
The system is built with a clear separation of concerns:
- **Backend:** `main.py`, `auth.py`, `models.py`, `database.py`.
- **Frontend:** `index.html`, `dashboard.html`, `admin.html`, and a suite of JS modules.

## 10. Testing
- **Auth Test:** Verified registration and secure JWT login.
- **Role Test:** Verified that users cannot access admin routes.
- **CRUD Test:** Verified complaint lifecycle from 'Pending' to 'Resolved'.

## 11. Advantages
- **Elasticity:** Scales with user demand.
- **Availability:** 99.9% uptime via cloud infrastructure.
- **Security:** Encrypted passwords and tokenized sessions.

## 12. Future Enhancements
- Email notifications using AWS SES.
- Priority-based sorting (High/Medium/Low).
- AI-based complaint categorization.

## 13. Conclusion
The Cloud-Based CMS successfully demonstrates the power of cloud models in building scalable, secure, and user-centric enterprise applications.
