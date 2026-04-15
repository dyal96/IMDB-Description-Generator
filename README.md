<p align="center">
  <img src="https://img.shields.io/badge/IMDb-Report_Generator-f5c518?style=for-the-badge&logo=imdb&logoColor=black" alt="IMDb Report Generator"/>
</p>

<h1 align="center">🎬 IMDb Movie & Series Report Generator</h1>

<p align="center">
  <b>One-click tool to fetch IMDb data for your video library, generate a stunning HTML report, and batch-rename files with IMDb ratings.</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.8+"/>
  <img src="https://img.shields.io/badge/platform-Windows-0078D6?style=flat-square&logo=windows&logoColor=white" alt="Windows"/>
  <img src="https://img.shields.io/badge/API-OMDb-f5c518?style=flat-square&logo=imdb&logoColor=black" alt="OMDb API"/>
  <img src="https://img.shields.io/badge/license-MIT-22c55e?style=flat-square" alt="MIT License"/>
</p>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📂 **Folder Picker** | Double-click to launch — select any folder via GUI dialog |
| 🔍 **Smart Title Detection** | Extracts clean movie/series names from messy filenames (strips quality tags, codecs, release groups, etc.) |
| 🌐 **IMDb Data Fetching** | Fetches ratings, genres, directors, cast, plot, posters & more via OMDb API |
| 📊 **Beautiful HTML Report** | Generates a premium dark-themed report with search, filters, sorting & poster thumbnails |
| 📝 **Rename Batch File** | Auto-generates a `.bat` file to prepend IMDb ratings to filenames (e.g., `8.9_breaking_bad.mp4`) |
| ⚡ **Smart Caching** | Caches API responses locally — no redundant lookups on re-runs |
| 🎯 **Auto-Detection** | Distinguishes movies from TV series automatically |
| 📈 **Progress Window** | Live GUI showing real-time lookup status with color-coded results |

---

## 🚀 Quick Start

### 1. Get a Free API Key

Sign up for a **free OMDb API key** (takes 30 seconds):  
👉 **https://www.omdbapi.com/apikey.aspx**

> Free tier allows **1,000 requests/day** — more than enough for most libraries.

### 2. Clone the Repository

```bash
git clone https://github.com/yourusername/imdb-report-generator.git
cd imdb-report-generator
```

### 3. Install Dependencies

```bash
pip install requests
```

> Or just double-click `run_movie_report.bat` — it installs dependencies automatically.

### 4. Run

**Option A** — Double-click `run_movie_report.bat`

**Option B** — Run from terminal:
```bash
python generate_movie_report.py
```

### 5. Follow the Prompts

1. Enter your OMDb API key (first run only — saved to `omdb_config.json`)
2. Select a folder containing video files
3. Wait for lookups to complete
4. Report opens automatically in your browser! 🎉

---

## 📸 What You Get

### HTML Report (`imdb_report.html`)

- 🏠 **Stats Dashboard** — Total files, movies, series, average rating at a glance
- 🔍 **Search & Filter** — Search by title, genre, director; filter by movies/series
- 📊 **Sortable Table** — Sort by rating, title, or year
- 🖼️ **Poster Thumbnails** — Movie posters fetched directly from IMDb
- 🏆 **Top 10** — Highest rated titles highlighted
- ⚠️ **Unmatched Files** — List of files that couldn't be found on IMDb

### Rename Batch File (`rename_with_ratings.bat`)

Generates ready-to-run rename commands:

```
Before:  Breaking.Bad.S01.720p.BluRay.x264.mp4
After:   9.5_breaking_bad_s01_720p_bluray_x264.mp4

Before:  The.Dark.Knight.2008.1080p.mkv
After:   9.0_the_dark_knight_2008_1080p.mkv
```

> ⚠️ The batch file asks for confirmation before renaming. Press `Ctrl+C` to cancel.

---

## 📁 Project Structure

```
imdb-report-generator/
├── generate_movie_report.py   # Main script
├── run_movie_report.bat       # Double-click launcher (Windows)
├── omdb_config.json           # API key config (auto-created)
├── imdb_cache.json            # Cached API responses (auto-created)
├── imdb_report.html           # Generated HTML report (output)
├── rename_with_ratings.bat    # Generated rename script (output)
└── README.md
```

---

## 🎬 Supported Video Formats

```
.mp4  .mkv  .avi  .mov  .ts  .m4v  .wmv
.flv  .webm  .mpg  .mpeg  .m2ts  .vob  .3gp
```

---

## 🧹 Smart Filename Cleaning

The script intelligently strips junk from filenames to extract the actual title:

| Input Filename | Extracted Title |
|---|---|
| `Breaking.Bad.S01E01.720p.BluRay.x264-DEMAND.mkv` | `Breaking Bad` |
| `The.Dark.Knight.2008.1080p.BluRay.x265.HEVC.mp4` | `The Dark Knight` |
| `Inception (2010) [1080p] [BluRay] [5.1].mp4` | `Inception` |
| `Money.Heist.S01.COMPLETE.NF.WEB-DL.mkv` | `Money Heist` |
| `Interstellar.2014.IMAX.2160p.UHD.BluRay.mp4` | `Interstellar` |

Strips: resolution tags, codecs (x264/x265/HEVC), source tags (BluRay/WEB-DL), audio tags (AAC/DTS/Atmos), release groups, file sizes, and more.

---

## ⚙️ Configuration

### `omdb_config.json`

```json
{
  "api_key": "your_api_key_here"
}
```

The API key is saved automatically on first run. To change it, edit this file or delete it to be prompted again.

### Cache (`imdb_cache.json`)

API responses are cached locally. Delete this file to force fresh lookups on the next run.

---

## 🛠️ Requirements

- **Python** 3.8 or higher
- **requests** library (`pip install requests`)
- **tkinter** (included with Python on Windows)
- **OMDb API key** ([free signup](https://www.omdbapi.com/apikey.aspx))

---

## 📋 FAQ

<details>
<summary><b>How do I get an OMDb API key?</b></summary>

1. Go to https://www.omdbapi.com/apikey.aspx
2. Select the **Free** tier (1,000 daily limit)
3. Enter your email and submit
4. Check your email and activate the key
5. Enter the key when the script prompts you

</details>

<details>
<summary><b>Can I scan subfolders?</b></summary>

Yes! The script scans one level of subdirectories. This handles the common case of series stored in their own folders (e.g., `Movies/Breaking Bad/episode.mp4`).

</details>

<details>
<summary><b>What if a movie isn't found?</b></summary>

The script tries multiple strategies:
1. Search as the detected type (movie/series)
2. Retry as the opposite type
3. Retry without the year filter

Unmatched files are listed in the report's **"Not Found"** section with the search term used, so you can verify the title extraction.

</details>

<details>
<summary><b>Is the rename reversible?</b></summary>

The generated `rename_with_ratings.bat` only renames files — it doesn't delete anything. However, renaming is not automatically reversible. Back up important files before running the batch script.

</details>

<details>
<summary><b>Does it work on macOS/Linux?</b></summary>

The Python script's core functionality works cross-platform. However, the `.bat` launcher and rename batch file are Windows-specific. The folder picker dialog uses `tkinter` which works on all platforms.

</details>

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Made with ❤️ for movie lovers<br>
  <sub>Powered by <a href="https://www.omdbapi.com/">OMDb API</a></sub>
</p>
