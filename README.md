# 🧢 Pokémon Nuzlocke Tracker

A full-featured application for tracking, storing, and analyzing **Nuzlocke challenge progress** across multiple Pokémon games.  
The tracker provides a structured way to record your runs, view previous progress, and plan future encounters, routes, and battles.

---

## 🎯 Overview

The **Pokémon Nuzlocke Tracker** allows players to log their journey through any main-series Pokémon game, complete with route progression, encounter data, and trainer battles.  
It provides an interactive way to **plan, record, and review** each run while maintaining data consistency across devices.

---

## ⚙️ Current Features

- **CLI Interface:**  
  Fully functional command-line interface as the backend foundation for future web integration.

- **Comprehensive Game Walkthrough Data:**  
  Automatically loads and structures every route, trainer, and encounter from mainline Pokémon games.  
  For example, a new run begins on Route 1 with access to all relevant Pokémon encounter data and upcoming locations.

- **Progress Tracking:**  
  Stores progression per run, including current team, defeated trainers, and caught Pokémon.

- **Data Persistence:**  
  Progress and route data are stored in a **PostgreSQL** database for structured querying and cross-run analytics.

---

## 🧩 Tech Stack

| Layer | Technology |
|-------|-------------|
| **Language** | Python |
| **Web Scraping / Data Aggregation** | BeautifulSoup, PokeAPI |
| **Database** | PostgreSQL |
| **Architecture** | CLI-based backend as a simulation of app's core logic |

---

## 🚀 Future Roadmap

### 1. Web & Mobile Application
- Frontend development for browser and mobile environments.
- Integration with RESTful APIs for full user interaction and account-based tracking.

### 2. Offline Data Synchronization
- Implementation of **dynamic local databases** (e.g., IndexedDB / SQLite) for users to update and store progress offline.
- Automatic synchronization once reconnected.

### 3. Save File Integration
- Reverse-engineering `.sav` files to import real in-game progress directly into the tracker.
- Automatic updating of Pokémon, routes, and badges from user save data.

---

