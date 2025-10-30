# 🏨 Booking Automation CLI (Selenium Project)

This is a **learning and demonstration project** built in **Python** using **Selenium WebDriver**.  
It automates hotel searches on [Booking.com](https://www.booking.com) and provides a fully **interactive command-line interface (CLI)** that lets you explore **real-world browser automation**, **web scraping logic**, and **terminal-based user interaction** in one place.

---

## 🌐 Project Overview

The goal of this project is to **understand Selenium-based automation in a real-world web environment** — not just simple button clicks, but dynamic page handling, element waits, safe retries, and user-driven workflows.

This project combines:
- 🧠 **Web Automation** — controlling and scraping live Booking.com data using Selenium  
- 💻 **CLI Interaction** — guiding users step-by-step through configuration  
- ⚙️ **Robust Script Design** — structured, modular Python classes with error handling  
- 🎯 **Practical Learning Objective** — bridging the gap between theoretical Selenium scripts and realistic automation tasks  

It’s perfect for students, developers, and testers who want to **learn browser automation with real website interaction** instead of artificial test pages.

---

## 🚀 Features

- ✅ **Selenium-based browser automation** with ChromeDriver auto-management  
- ✅ **Interactive CLI (menu-driven)** to simulate user workflows in the terminal  
- ✅ **Safe waits, retries, and exception handling** for unstable or dynamic web pages  
- ✅ **Flexible date and guest selection** using real Booking.com controls  
- ✅ **Filter, price range, and sorting options** applied dynamically  
- ✅ **PrettyTable integration** for clean tabular output  
- ✅ **Optional CSV export** to save extracted hotel data  
- ✅ **Educational focus** — built to teach web automation and CLI development

---

## 🧩 Project Structure

booking-automation-cli/
│
├── BookingsBot/
│ ├── booking.py # Core Selenium automation logic
│ ├── constants.py # Constants (colors, filters, sort options)
│ ├── init.py # Package initializer
│
├── interactive_cli.py # Main entry point: interactive menu-driven CLI
├── run.py # Hardcoded non-interactive demo
├── requirements.txt # Dependencies list
└── README.md # Documentation


## ⚙️ Requirements

You’ll need **Python 3.8+** and **Google Chrome** installed.

Install dependencies with:

```bash
pip install -r requirements.txt
