# StyleCart — Fashion Store Demo

A local fashion e-commerce learning project built with Flask, SQLite, HTML, CSS and JavaScript. The layout is inspired by modern fashion marketplaces; it does not use Myntra branding.

## Features
- Product listing, search, category filter, maximum price filter, sorting
- Product detail pages and image cards
- Session-based shopping bag with quantity update/removal
- Registration and login with hashed passwords
- Checkout form and saved order history (demo checkout; no real payment)
- Content-based ML recommendations using TF-IDF vectors and cosine similarity on product text
- Responsive styling

## Requirements
- Windows 10/11
- Python 3.10 or newer
- Internet connection for the remote Unsplash product images (you can replace these with local images later)

## Run on Windows

Open PowerShell in this project folder:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

If PowerShell blocks activation, run this only for the current terminal:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Open `http://127.0.0.1:5000` in your browser.

## If you already have a Python/Streamlit project
Do not overwrite your existing project first. Make a backup or create a separate folder named `stylecart_fashion_store`, extract this ZIP there, and run the commands above from that new folder. This keeps your phishing detector project safe.

## Demo flow
1. Open the home page and browse products.
2. Use search, filters and sorting on Shop.
3. Add a product to the bag.
4. Register using a test email and a password of at least 8 characters.
5. Open the bag and continue to checkout.
6. Submit demo delivery details and view the confirmation/order history.

## Notes
- This is a local educational prototype, not a production store.
- Checkout records an order in SQLite but does not process payments or ship goods.
- Recommendations use TF-IDF and cosine similarity over product names, categories, subcategories and descriptions. This is a small content-based ML demo, not a large production recommender.
- Product images load from Unsplash URLs and require internet access.
- Before deploying publicly: set a strong `SECRET_KEY`, disable debug mode, add CSRF protection and rate limiting, validate all inputs, add proper payment/shipping integrations, and review privacy/security requirements.
