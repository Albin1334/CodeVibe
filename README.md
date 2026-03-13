# CodeVibe
# Medi book: 100% Offline AI Health Assistant
Medi book is a completely private, air-gapped AI health and wellness assistant. Built for areas with low connectivity and users who prioritize absolute data security, this app runs entirely on your local hardware without ever sending a single byte of patient data to the cloud.

## The Problem
Modern AI health tools rely on centralized cloud servers (like OpenAI or Google Cloud). This creates three massive barriers in healthcare:
1. Data Vulnerability: Sensitive medical queries are transmitted over the internet, risking HIPAA/GDPR violations and data breaches.
2. Connectivity:Patients in rural or low-bandwidth environments are cut off from modern AI triaging tools.

## Our Solution
Medi book bypasses the cloud entirely. By leveraging on-device Large Language Models (LLMs) via Ollama, we bring the intelligence of modern AI directly to the user's local machine. 

## Technology Stack
Medi book was intentionally built without bloated frontend frameworks or cloud dependencies.
* AI Engine:[Ollama](https://ollama.com/) (running `tinyllama` for rapid CPU inference)
* Backend: Python 3 & Flask
* Database: SQLite3 (Built-in, Serverless)
* Frontend: Pure HTML5 & CSS3 (No JavaScript, utilizing Server-Side Rendering)

## How to Run Locally

### Prerequisites
1. Install [Python](https://www.python.org/downloads/) (Make sure to check "Add to PATH" during installation).
2. Install [Ollama](https://ollama.com/download).

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/yourusername/medibook.git](https://github.com/yourusername/medibook.git)
   cd medibook
