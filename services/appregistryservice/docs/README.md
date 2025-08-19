# Application Registry Service

A REST API service for registering and managing applications. This service provides endpoints for application registration, retrieval, updates, and management with comprehensive validation and error handling.

## Features

- **Application Registration**: Register new applications with detailed metadata
- **CRUD Operations**: Create, Read, Update, and Delete applications
- **API Key Management**: Automatic API key generation and regeneration
- **Filtering**: Filter applications by status, platform, and category
- **Input Validation**: Comprehensive validation using Marshmallow schemas
- **Error Handling**: Robust error handling with meaningful error messages
- **Database Support**: SQLite database with SQLAlchemy ORM
- **CORS Support**: Cross-origin resource sharing enabled

## Quick Start

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Clone or navigate to the project directory:
```bash
cd appregistryservice
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database:
```bash
python init_db.py
```

4. Run the development server:
```bash
python app.py
```

The service will be available at `http://localhost:5000`

### Production Deployment

For production deployment, use:
```bash
python run.py
```

Or with Gunicorn:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

## API Endpoints

### Health Check
- **GET** `/health` - Health check endpoint

### Application Management

#### Register Application
- **POST** `/api/applications`
- **Description**: Register a new application
- **Request Body**:
```json
{
  "name": "My Application",
  "description": "Application description",
  "version": "1.0.0",
  "developer": "Developer Name",
  "contact_email": "developer@example.com",
  "category": "productivity",
  "platform": "web"
}
```
- **Response**: Application object with generated ID and API key

#### Get All Applications
- **GET** `/api/applications`
- **Description**: Retrieve all registered applications
- **Query Parameters**:
  - `status`: Filter by status (active, inactive, pending)
  - `platform`: Filter by platform (web, mobile, desktop, api)
  - `category`: Filter by category
- **Response**: Array of application objects

#### Get Application by ID
- **GET** `/api/applications/{id}`
- **Description**: Retrieve a specific application by ID
- **Response**: Application object

#### Update Application
- **PUT** `/api/applications/{id}`
- **Description**: Update an existing application
- **Request Body**: Partial application object with fields to update
- **Response**: Updated application object

#### Delete Application
- **DELETE** `/api/applications/{id}`
- **Description**: Delete an application
- **Response**: Success message

#### Regenerate API Key
- **POST** `/api/applications/{id}/regenerate-key`
- **Description**: Generate a new API key for the application
- **Response**: New API key

## Data Model

### Application Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | String | Auto-generated | Unique identifier (UUID) |
| name | String | Yes | Application name (max 100 chars) |
| description | Text | No | Application description |
| version | String | Yes | Application version (max 20 chars) |
| developer | String | Yes | Developer name (max 100 chars) |
| contact_email | Email | Yes | Developer contact email |
| category | String | No | Application category (max 50 chars) |
| platform | String | No | Platform type (web, mobile, desktop, api) |
| status | String | Auto-set | Status (active, inactive, pending) |
| api_key | String | Auto-generated | Unique API key |
| created_at | DateTime | Auto-set | Creation timestamp |
| updated_at | DateTime | Auto-updated | Last update timestamp |

## Example Usage

### Register a New Application

```bash
curl -X POST http://localhost:5000/api/applications \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Weather App",
    "description": "A simple weather application",
    "version": "2.1.0",
    "developer": "John Doe",
    "contact_email": "john@example.com",
    "category": "weather",
    "platform": "mobile"
  }'
```

### Get All Applications

```bash
curl http://localhost:5000/api/applications
```

### Filter Applications by Platform

```bash
curl http://localhost:5000/api/applications?platform=mobile
```

### Update an Application

```bash
curl -X PUT http://localhost:5000/api/applications/{app_id} \
  -H "Content-Type: application/json" \
  -d '{
    "version": "2.2.0",
    "description": "Updated weather application with new features"
  }'
```

### Regenerate API Key

```bash
curl -X POST http://localhost:5000/api/applications/{app_id}/regenerate-key
```

## Error Handling

The API returns appropriate HTTP status codes and error messages:

- **400 Bad Request**: Validation errors
- **404 Not Found**: Resource not found
- **409 Conflict**: Duplicate application name
- **500 Internal Server Error**: Server errors

Error response format:
```json
{
  "error": "Error description",
  "details": {
    "field": ["Specific validation error"]
  }
}
```

## Configuration

The application can be configured using environment variables:

- `FLASK_APP`: Application entry point (default: app.py)
- `FLASK_ENV`: Environment (development/production)
- `DATABASE_URL`: Database connection string (default: sqlite:///app_registry.db)
- `SECRET_KEY`: Flask secret key for sessions

## Development

### Project Structure

```
appregistryservice/
├── app.py              # Main Flask application
├── models.py           # Database models
├── schemas.py          # Validation schemas
├── config.py           # Configuration settings
├── init_db.py          # Database initialization
├── run.py              # Production runner
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

### Running Tests

To test the API endpoints, you can use the provided curl examples or tools like Postman.

## License

This project is part of the Etn-Electrical IzumaPOC and is intended for internal use.

## Support

For questions or issues, please contact the development team.
