# Gift of Shiva - Flask Version

This is a Flask version of the Gift of Shiva cannabis website.

## Setup Instructions

1. **Clone the repository**

2. **Set up a virtual environment** (recommended)
   ```
   python -m venv venv
   ```

3. **Activate the virtual environment**
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS and Linux:
     ```
     source venv/bin/activate
     ```

4. **Install dependencies**
   ```
   pip install -r requirements.txt
   ```

5. **Run the application**
   ```
   python app.py
   ```

6. **Access the website**
   - Open your web browser and navigate to `http://127.0.0.1:5000`

## Admin Access

- URL: `http://127.0.0.1:5000/admin/login`
- Username: `admin`
- Password: `password`

## Features

- Responsive design for desktop and mobile devices
- Product catalog with filtering options
- Admin dashboard for product management
- User-friendly interface for browsing products

## Project Structure

- `/static` - Contains all static files (CSS, JavaScript, images)
- `/templates` - Contains all HTML templates
- `app.py` - Main Flask application file
- `products.json` - Sample product data (created on first run)

## Technologies Used

- Flask
- Bootstrap 5
- Font Awesome
- JavaScript
- JSON for data storage 