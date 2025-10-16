# 🧠 PriceOracle
**Smart Price Comparison Web App**  
A project by the Smart Price Comparison team.

---

## 📖 Overview
PriceOracle is a web app that helps users find the **lowest product price** across top e-commerce sites — **Amazon**, **Flipkart**, and **Myntra**.  
Users enter a product name, and the app fetches data from these platforms using **async scraping**, then displays:
- Product title  
- Price on each platform  
- Direct buy link  
- Highlighted **lowest price**

---

## ⚙️ Features
- Compare prices across Amazon, Flipkart, and Myntra  
- Display product list with images, titles, and prices dynamically  
- Show **“Lowest Price”** with clickable link to buy  
- Responsive web interface using **React + Tailwind CSS**  
- Future scope: user login, price alerts, wishlist tracking, and analytics  

---

## 🏗️ Tech Stack

| Area | Choice | Why it’s ideal |
|------|--------|----------------|
| **Backend Framework** | 🟢 FastAPI | Async support + automatic docs (Swagger UI) + type hints = modern and fast. Handles parallel scrapes efficiently. |
| **HTTP Client** | 🟣 aiohttp | Perfect for FastAPI. Hit Amazon, Flipkart, and Myntra simultaneously for fast results. |
| **Scraping Library** | 🟢 BeautifulSoup4 | Simple, fast, and easy to maintain. Perfect for scraping a few platforms. |
| **Database** | 🟣 MongoDB (with Motor) | Async-friendly and flexible schema. Fits product data variations seamlessly. |
| **Frontend** | 🔵 React + Tailwind CSS | Ideal for dynamic UI — product comparison grid or card-style layout. |
| **Data Handling** | 🟢 pandas (optional) | Useful for sorting/filtering cached results before displaying. |
| **Cache / Local Store** | 🟣 TinyDB (optional) | Lightweight local option for testing before hooking MongoDB. |
| **Environment Management** | 🧩 Miniconda + environment.yml | Ensures reproducible environment setup for all developers. |

---

## 🚀 Setup Instructions

1. **Clone the repo**
   ```bash
   git clone https://github.com/Smart-Price-Comparison/PriceOracle.git
   cd PriceOracle
