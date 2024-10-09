# Django Brewing Project

## Overview

This Django-based web application is designed for home brewers to manage their brewing process, from creating batches to sharing finished products. It allows users to track ingredients, monitor the brewing process, and share their creations with other users.

## Features

- User authentication and authorization
- Batch creation and management
- Batch tracking with QR code generation
- Ingredient tracking
- Process entry logging
- Finished product management
- Bottle tracking with QR code generation
- Product sharing among users
- Liking system for shared products

## Prerequisites

- Python 3.11+
- pip
- virtualenv (recommended)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/darcccas/django-brewing-project.git
   cd django-brewing-project
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Unix or MacOS
   venv\Scripts\activate  # On Windows
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up the database:
   ```
   python manage.py migrate
   ```

5. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

6. Run the development server:
   ```
   python manage.py runserver
   ```

The application should now be running at `http://127.0.0.1:8000/`.

## Usage

1. Log in to the application using your superuser credentials.
2. Create a new batch by navigating to "Add Batch" and filling in the required information.
3. Add ingredients and process entries to your batch as you progress.
4. When your batch is complete, finish it to create a finished product.
5. Add bottles to your finished product and generate QR codes for them.
6. Share your finished product with other users.
7. View shared products from other users and like them if you wish.

## Project Structure

- `models.py`: Contains the database models for Ingredient, Batch, FinishedProduct, Bottle, SharedProduct, and ProductLike.
- `views.py`: Contains the view functions for handling HTTP requests.
- `urls.py`: Defines the URL patterns for the application.
- `templates/`: Contains HTML templates for rendering pages.
- `static/`: Contains static files such as CSS, JavaScript, and images.

## Contributing

If you'd like to contribute to this project, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and commit them with descriptive commit messages.
4. Push your changes to your fork.
5. Submit a pull request to the main repository.

## License

[Specify your chosen license here, e.g., MIT, GPL, etc.]

## Contact

Dar Com ™ - darccas@gmail.com

Project Link: https://github.com/darcccas/django-brewing-project

