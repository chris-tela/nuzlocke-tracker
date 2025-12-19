# 🧢 Pokémon Nuzlocke Tracker

A full-featured application for tracking, storing, and analyzing **Nuzlocke challenge progress** across multiple Pokémon games.  
The tracker provides a structured way to record your runs, view previous progress, and plan future encounters, routes, and battles.

---

## 🎯 Overview

The **Pokémon Nuzlocke Tracker** allows players to log their journey through any main-series Pokémon game, complete with route progression, encounter data, and trainer battles.  
It provides an interactive way to **plan, record, and review** each run while maintaining data consistency across devices.

---

## ⚙️ Current Features

- **Full-Stack Functionality:**  
  While a playable CLI is still available, the project now includes a web app in development for a more interactive experience.

- **Comprehensive Pokémon Database:**  
  Includes all Pokémon data, gym trainers, and movesets, allowing for complete team management and strategic planning.

- **Ordered Walkthrough Data:**  
  Structured routes and trainer encounters for every mainline Pokémon game, providing a guided progression for each run.

- **Team Management & Storage:**  
  Tracks player teams, including caught Pokémon, stats, and progress across multiple runs.

- **Progress Tracking:**  
  Stores run-specific data such as current location, defeated trainers, and captured Pokémon.

- **Data Persistence:**  
  Progress, route, and team data are stored in **PostgreSQL** and **SQLite** databases for structured querying and analytics.

- **Future-Ready Architecture:**  
  Supporting upcoming features like interactive battle simulations and matchup analysis.


## 🧩 Tech Stack

| Layer | Technology |
|-------|-------------|
| **Language** | Python, TypeScript |
| **Web Scraping / Data Aggregation** | BeautifulSoup, PokeAPI |
| **Frontend / UI** | React |
| **Authentication** | OAuth, JWT |
| **Database** | PostgreSQL, SQLite |

---

## 🚀 Future Roadmap

### 1. Web & Mobile Application (work in progress!)
- Frontend development for browser and mobile environments.
- Integration with RESTful APIs for full user interaction and account-based tracking.

### 2. Offline Data Synchronization
- Implementation of **dynamic local databases** (e.g., IndexedDB / SQLite) for users to update and store progress offline.
- Automatic synchronization once reconnected.

### 3. Save File Integration
- Reverse-engineering `.sav` files to import real in-game progress directly into the tracker.
- Automatic updating of Pokémon, routes, and badges from user save data.

### 4. Damage Calculator & Matchup Synergy
- Calculates expected damage for moves based on stats, type advantages, and in-game conditions.  
- Evaluates Pokémon pairings to highlight synergy, helping players plan strategies.


---

