# Placement Portal

A web application for managing student placements, internships, and job applications.

## Features

- Student registration and login
- Company and opportunity management 
- Application tracking
- Skills management
- Interview scheduling

## Tech Stack

- **Backend**: Python with Flask
- **Database**: MySQL
- **Frontend**: HTML, CSS, JavaScript with Bootstrap 5

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- MySQL Server
- pip (Python package manager)

### Step 1: Clone the repository

```bash
git clone <repository-url>
cd placement_portal
```

### Step 2: Create a virtual environment

```bash
python -m venv venv
```

#### On Windows:
```bash
venv\Scripts\activate
```

#### On macOS/Linux:
```bash
source venv/bin/activate
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Setup Database

Run the SQL script in `database/schema.sql` to create the database and tables:

```bash
mysql -u root -p < database/schema.sql
```

Alternatively, you can manually run the SQL commands in the file using a MySQL client.

### Step 5: Configure environment variables

Copy the `.env.example` file to `.env` and update the values:

```bash
cp .env.example .env
```

Edit the `.env` file to set your database credentials and other configuration.

### Step 6: Run the application

```bash
python app.py
```

The application will start and be available at `http://localhost:5000`.

## Project Structure

- `app.py` - Main application file
- `templates/` - HTML templates
- `static/` - Static files (CSS, JS, images)
- `uploads/` - Upload directory for resumes
- `database/` - Database schemas and scripts

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Contact

Your Name - your.email@example.com

Project Link: [https://github.com/yourusername/placement_portal](https://github.com/yourusername/placement_portal) 