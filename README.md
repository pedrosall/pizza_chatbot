# 🍕 PizzaBot Pro: AI-Driven Conversational Commerce Prototype

> An experimental Telegram bot powered by LLMs for automated pizza order management, integrated with a real-time Streamlit analytics dashboard and fully containerized via Docker.

---

## ⚠️ Project Status: Paused Prototype / Work in Progress

> **Notice:** This repository is an architecture prototype and is currently **not production-ready**. Development has been paused. The core infrastructure, containerization, and LLM orchestration are functional, but the project contains known edge-case bugs, state-machine vulnerabilities, and unhandled exceptions during high-concurrency simulation. It is kept public as a showcase of tech stack integration and LLM parsing capabilities.

---

## 🛠️ Tech Stack & Libraries

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![Telegram](https://img.shields.io/badge/Telegram-%232CA5E0.svg?style=for-the-badge&logo=telegram&logoColor=white) ![Google Gemini](https://img.shields.io/badge/Google%20Gemini-8E75FF?style=for-the-badge&logo=googlegemini&logoColor=white) ![Streamlit](https://img.shields.io/badge/Streamlit-%23FF4B4B.svg?style=for-the-badge&logo=Streamlit&logoColor=white) ![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)

---

## 🎯 Core Features

* **Natural Language Order Processing (NLP):** Integrates Google Gemini AI to analyze raw customer text inputs, extracting intents, pizza types, quantities, and delivery addresses without forcing static command inputs.
* **Asynchronous Bot Architecture:** Built on top of `aiogram` to handle non-blocking concurrent user interactions smoothly.
* **Business Dashboard:** A `Streamlit` analytical view linked to the bot's data layer to monitor incoming orders, processing times, and revenue metrics.
* **Multi-Container Orchestration:** Standardized environment using `Docker` and `Docker Compose` to launch both the asynchronous bot service and the visualization dashboard simultaneously.

---

## 🛠️ Current Repository Architecture

* 📁 `app/` - Core logic directory containing the data storage layer and dashboard configuration.
* 📄 `telegram_bot.py` - Main entry point orchestrating the asynchronous loop, `aiogram` handlers, and Gemini API middleware.
* 📄 `Dockerfile` & `docker-compose.yml` - Complete multi-stage container definitions.
* 📄 `.env.example` - Template showing the required environment variables.

---

## 🔧 Quick Installation (Local Deployment)

To run the current state of the prototype locally:

1. Clone the repository:
   ```bash
   git clone [https://github.com/pedrosall/your-repo-name.git](https://github.com/pedrosall/your-repo-name.git)
