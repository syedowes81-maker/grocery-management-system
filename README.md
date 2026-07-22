# FreshCart - Grocery Management System

## About the Project

FreshCart is a grocery shopping web application developed using Flask and SQLite.
It allows users to browse grocery items, add products to a shopping cart, place orders, and generate invoices. This project was built to practice backend development, database management, and web application development using Python.

## Features

- User login
- Browse products by category
- Add and remove items from the cart
- Update product quantity
- Place orders
- Generate PDF invoices
- User dashboard
- Custom error page
- Health check and version endpoints

## Project Highlights

- Clean and simple user interface
- Category-based product browsing
- Shopping cart with quantity management
- PDF invoice generation
- SQLite database integration
- Session-based authentication

## Technologies Used

- Python
- Flask
- SQLite
- HTML
- CSS
- JavaScript
- ReportLab

## Project Structure

FreshCart/
├── app.py                  # Main Flask application
├── templates/              # HTML templates
├── static/
│   ├── css/                # Stylesheets
│   └── images/             # Product images
├── screenshots/            # Project screenshots
├── freshcart.db            # SQLite database
├── requirements.txt        # Project dependencies
├── README.md               # Project documentation
├── CHANGELOG.md            # Project updates
├── LICENSE                 # MIT License
└── Procfile                # Deployment configuration

## Current Limitations

- User roles are basic and can be improved.
- Product images are stored locally.
- Payment integration is not available.
- Email notifications are not implemented.
- The application is intended for learning and demonstration purposes.

## Planned Improvements

- Add product search and filtering
- Add product reviews and ratings
- Allow users to track previous orders
- Improve the admin dashboard
- Integrate an online payment gateway
- Improve the mobile experience
- Add email notifications for orders
- Add inventory management for administrators

## How to Run

1. Clone the repository.
2. Install the required packages using:
pip install -r requirements.txt
3. Start the application:
python3 app.py
4. Open the application in your browser.

## How to Use

1. Register or log in to your account.
2. Browse products by category.
3. Add products to your shopping cart.
4. Update product quantities if needed.
5. Place an order.
6. Download the generated PDF invoice.
7. View your dashboard.

## What I Learned

While building this project, I gained practical experience with:

- Building web applications using Flask
- Working with SQLite databases
- Managing user sessions and authentication
- Creating shopping cart functionality
- Generating PDF invoices using ReportLab
- Organizing templates and static files
- Using Git and GitHub for version control

## Author

Developed by **Syed Owes Jaleel** as a personal learning project.

## Screenshots

### Login

![Login](screenshots/login.png)

### Dashboard

![Dashboard](screenshots/dashboard.png)

### Products

![Products](screenshots/products.png)

### Product Details

![Product Details](screenshots/productinfo.png)

### Shopping Cart

![Shopping Cart](screenshots/cart.png)

### Invoice

![Invoice](screenshots/invoice.png)
