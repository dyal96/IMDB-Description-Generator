"""
IMDb Movie & Web Series Report Generator
=========================================
Double-click this script (or run_movie_report.bat) to:
  1. Pick a folder containing video files
  2. Fetch IMDb data (rating, genre, year, plot, etc.) for each title
  3. Generate a beautiful HTML report in the script's directory
  4. Generate a batch file to rename videos with IMDb ratings prepended

Requires: pip install requests
OMDb API Key: Get a free key at https://www.omdbapi.com/apikey.aspx
"""

import os
import sys
import re
import json
import time
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from datetime import datetime

# ─── Configuration ──────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "omdb_config.json")
CACHE_FILE = os.path.join(SCRIPT_DIR, "imdb_cache.json")

VIDEO_EXTENSIONS = {
    '.mp4', '.mkv', '.avi', '.mov', '.ts', '.m4v', '.wmv',
    '.flv', '.webm', '.mpg', '.mpeg', '.m2ts', '.vob', '.3gp'
}

# Junk words commonly found in torrent/release filenames
JUNK_PATTERNS = [
    # Quality tags
    r'\b(2160p|1080p|720p|480p|360p|4k|uhd|hdr|hdr10|hdr10plus|dolby\s*vision)\b',
    # Source tags
    r'\b(bluray|blu-ray|bdrip|brrip|webrip|web-dl|webdl|web\s*dl|hdtv|dvdrip|dvdscr|hdcam|cam|camrip|ts|telesync|hdrip|amzn|nf|dsnp|hmax|atvp|pcok|ma)\b',
    # Codec tags
    r'\b(x264|x265|h264|h\.264|h265|h\.265|hevc|avc|xvid|divx|av1|10bit|8bit)\b',
    # Audio tags
    r'\b(aac|ac3|dts|dts-hd|truehd|atmos|dd5\.1|dd7\.1|5\.1|7\.1|eac3|flac|mp3|opus)\b',
    # Release group tags (common patterns)
    r'\[.*?\]',
    r'\(.*?\)',
    # Common release keywords
    r'\b(extended|unrated|directors\.cut|remastered|proper|repack|internal|limited|complete|season|s\d{1,2}e\d{1,2}|s\d{1,2})\b',
    # File size patterns
    r'\b\d+(\.\d+)?\s*(gb|mb)\b',
    # Misc junk
    r'\b(yts|yify|rarbg|ettv|eztv|sparks|geckos|tigole|qxr|joy|evo|flee|strife|ntb|cm|megusta|usury|nogrp)\b',
    r'\beng(lish)?\b',
    r'\bhindi\b',
    r'\bdual\s*audio\b',
    r'\bmulti\s*sub(s)?\b',
    r'\bsubtitle(s|d)?\b',
    r'\besub(s)?\b',
    r'\bwww\..*?\.com\b',
    r'\bwww\..*?\.org\b',
]

# ─── Helpers ────────────────────────────────────────────────────────────────────

def load_config():
    """Load or create OMDb API config."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_config(config):
    """Save OMDb API config."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


def load_cache():
    """Load IMDb data cache to avoid redundant API calls."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_cache(cache):
    """Save IMDb data cache."""
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def clean_filename(filename):
    """
    Extract a clean movie/series title from a messy filename.
    Examples:
        'Breaking.Bad.S01E01.720p.BluRay.x264.mp4' -> 'Breaking Bad'
        'The.Dark.Knight.2008.1080p.BluRay.mp4' -> 'The Dark Knight'
        'Inception (2010) [1080p].mkv' -> 'Inception'
    """
    # Remove extension
    name = os.path.splitext(filename)[0]

    # Replace dots, underscores with spaces
    name = name.replace('.', ' ').replace('_', ' ')

    # Try to extract year and truncate everything after it
    year_match = re.search(r'(^|\s)((?:19|20)\d{2})(\s|$)', name)
    if year_match:
        name = name[:year_match.start()].strip()

    # Try to detect season/episode markers and truncate
    season_match = re.search(r'\b[Ss]\d{1,2}([Ee]\d{1,2})?\b', name)
    if season_match:
        name = name[:season_match.start()].strip()

    # Remove junk patterns
    for pattern in JUNK_PATTERNS:
        name = re.sub(pattern, ' ', name, flags=re.IGNORECASE)

    # Remove any remaining brackets and their contents
    name = re.sub(r'\[.*?\]', ' ', name)
    name = re.sub(r'\(.*?\)', ' ', name)

    # Clean up whitespace
    name = re.sub(r'\s+', ' ', name).strip()

    # Remove trailing dashes or hyphens
    name = name.rstrip('- ')

    return name


def extract_year(filename):
    """Try to extract a year from the filename."""
    name = os.path.splitext(filename)[0].replace('.', ' ').replace('_', ' ')
    match = re.search(r'\b((?:19|20)\d{2})\b', name)
    return match.group(1) if match else None


def is_likely_series(filename):
    """Check if filename looks like a TV series episode."""
    name = filename.replace('.', ' ').replace('_', ' ')
    return bool(re.search(r'\b[Ss]\d{1,2}[Ee]\d{1,2}\b', name)) or \
           bool(re.search(r'\b[Ss]eason\s*\d+\b', name, re.IGNORECASE)) or \
           bool(re.search(r'\bEpisode\s*\d+\b', name, re.IGNORECASE)) or \
           bool(re.search(r'\b[Ss]\d{1,2}\b', name))


def fetch_imdb_data(title, api_key, year=None, media_type=None):
    """Fetch movie/series data from OMDb API."""
    import requests

    params = {
        't': title,
        'apikey': api_key,
        'plot': 'short',
    }
    if year:
        params['y'] = year
    if media_type:
        params['type'] = media_type  # 'movie' or 'series'

    try:
        resp = requests.get('https://www.omdbapi.com/', params=params, timeout=15)
        data = resp.json()

        if data.get('Response') == 'True':
            return {
                'title': data.get('Title', title),
                'year': data.get('Year', 'N/A'),
                'rated': data.get('Rated', 'N/A'),
                'runtime': data.get('Runtime', 'N/A'),
                'genre': data.get('Genre', 'N/A'),
                'director': data.get('Director', 'N/A'),
                'actors': data.get('Actors', 'N/A'),
                'plot': data.get('Plot', 'N/A'),
                'language': data.get('Language', 'N/A'),
                'country': data.get('Country', 'N/A'),
                'imdb_rating': data.get('imdbRating', 'N/A'),
                'imdb_votes': data.get('imdbVotes', 'N/A'),
                'imdb_id': data.get('imdbID', ''),
                'type': data.get('Type', 'N/A'),
                'poster': data.get('Poster', 'N/A'),
                'total_seasons': data.get('totalSeasons', 'N/A'),
                'awards': data.get('Awards', 'N/A'),
                'metascore': data.get('Metascore', 'N/A'),
                'box_office': data.get('BoxOffice', 'N/A'),
                'found': True,
            }
        else:
            return {'title': title, 'found': False, 'error': data.get('Error', 'Unknown error')}

    except Exception as e:
        return {'title': title, 'found': False, 'error': str(e)}


def scan_video_files(folder):
    """Scan folder for video files (non-recursive option available)."""
    videos = []
    for entry in os.listdir(folder):
        full_path = os.path.join(folder, entry)
        if os.path.isfile(full_path):
            ext = os.path.splitext(entry)[1].lower()
            if ext in VIDEO_EXTENSIONS:
                videos.append({
                    'filename': entry,
                    'filepath': full_path,
                    'extension': ext,
                    'size_mb': round(os.path.getsize(full_path) / (1024 * 1024), 1),
                })
        elif os.path.isdir(full_path):
            # Check if the subdirectory contains video files (for series folders)
            for sub_entry in os.listdir(full_path):
                sub_path = os.path.join(full_path, sub_entry)
                if os.path.isfile(sub_path):
                    ext = os.path.splitext(sub_entry)[1].lower()
                    if ext in VIDEO_EXTENSIONS:
                        videos.append({
                            'filename': sub_entry,
                            'filepath': sub_path,
                            'extension': ext,
                            'size_mb': round(os.path.getsize(sub_path) / (1024 * 1024), 1),
                            'subfolder': entry,
                        })
    return videos


def generate_html_report(results, folder_path, output_path):
    """Generate a beautiful HTML report."""

    found_results = [r for r in results if r.get('found')]
    not_found = [r for r in results if not r.get('found')]
    movies = [r for r in found_results if r.get('type') == 'movie']
    series = [r for r in found_results if r.get('type') == 'series']

    # Stats
    total = len(results)
    avg_rating = 0
    rated_count = 0
    for r in found_results:
        try:
            avg_rating += float(r['imdb_rating'])
            rated_count += 1
        except (ValueError, TypeError):
            pass
    avg_rating = round(avg_rating / rated_count, 1) if rated_count > 0 else 0

    # Top rated
    rated_items = []
    for r in found_results:
        try:
            rated_items.append((float(r['imdb_rating']), r))
        except (ValueError, TypeError):
            pass
    rated_items.sort(key=lambda x: x[0], reverse=True)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IMDb Report — {os.path.basename(folder_path)}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-primary: #0a0a0f;
            --bg-secondary: #12121a;
            --bg-card: #1a1a2e;
            --bg-card-hover: #222240;
            --border: #2a2a45;
            --text-primary: #e8e8f0;
            --text-secondary: #9898b0;
            --text-muted: #6868808;
            --accent-gold: #f5c518;
            --accent-blue: #4a9eff;
            --accent-purple: #a855f7;
            --accent-green: #22c55e;
            --accent-red: #ef4444;
            --accent-orange: #f97316;
            --gradient-gold: linear-gradient(135deg, #f5c518, #e8a800);
            --gradient-blue: linear-gradient(135deg, #4a9eff, #2563eb);
            --gradient-purple: linear-gradient(135deg, #a855f7, #7c3aed);
            --shadow-lg: 0 20px 60px rgba(0,0,0,0.5);
            --shadow-glow: 0 0 40px rgba(245,197,24,0.1);
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Inter', -apple-system, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
        }}

        /* Background effect */
        body::before {{
            content: '';
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background:
                radial-gradient(ellipse at 20% 0%, rgba(245,197,24,0.05) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 100%, rgba(74,158,255,0.05) 0%, transparent 50%);
            pointer-events: none;
            z-index: 0;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 40px 24px;
            position: relative;
            z-index: 1;
        }}

        /* ─── Header ─── */
        .header {{
            text-align: center;
            margin-bottom: 48px;
        }}

        .header-badge {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(245,197,24,0.1);
            border: 1px solid rgba(245,197,24,0.2);
            border-radius: 100px;
            padding: 6px 16px;
            font-size: 13px;
            color: var(--accent-gold);
            font-weight: 500;
            margin-bottom: 16px;
        }}

        .header h1 {{
            font-size: clamp(32px, 5vw, 56px);
            font-weight: 900;
            background: linear-gradient(135deg, #f5c518 0%, #ffffff 50%, #4a9eff 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: -1px;
            margin-bottom: 8px;
        }}

        .header p {{
            color: var(--text-secondary);
            font-size: 16px;
            max-width: 600px;
            margin: 0 auto;
        }}

        .header .folder-path {{
            font-family: 'Courier New', monospace;
            font-size: 13px;
            color: var(--text-muted);
            background: var(--bg-secondary);
            padding: 6px 14px;
            border-radius: 8px;
            border: 1px solid var(--border);
            display: inline-block;
            margin-top: 12px;
        }}

        /* ─── Stats Grid ─── */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 48px;
        }}

        .stat-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 24px;
            text-align: center;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}

        .stat-card::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 3px;
            border-radius: 16px 16px 0 0;
        }}

        .stat-card:nth-child(1)::before {{ background: var(--gradient-gold); }}
        .stat-card:nth-child(2)::before {{ background: var(--gradient-blue); }}
        .stat-card:nth-child(3)::before {{ background: var(--gradient-purple); }}
        .stat-card:nth-child(4)::before {{ background: linear-gradient(135deg, #22c55e, #10b981); }}
        .stat-card:nth-child(5)::before {{ background: linear-gradient(135deg, #f97316, #ea580c); }}

        .stat-card:hover {{
            transform: translateY(-4px);
            box-shadow: var(--shadow-lg);
            border-color: rgba(245,197,24,0.3);
        }}

        .stat-value {{
            font-size: 36px;
            font-weight: 800;
            color: var(--text-primary);
            margin-bottom: 4px;
        }}

        .stat-label {{
            font-size: 13px;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }}

        /* ─── Filter / Search ─── */
        .controls {{
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-bottom: 32px;
            align-items: center;
        }}

        .search-box {{
            flex: 1;
            min-width: 250px;
            position: relative;
        }}

        .search-box input {{
            width: 100%;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 12px 16px 12px 44px;
            color: var(--text-primary);
            font-size: 14px;
            font-family: 'Inter', sans-serif;
            outline: none;
            transition: border-color 0.3s;
        }}

        .search-box input:focus {{
            border-color: var(--accent-gold);
        }}

        .search-box::before {{
            content: '🔍';
            position: absolute;
            left: 14px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 16px;
        }}

        .filter-btn {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 10px 18px;
            color: var(--text-secondary);
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            font-family: 'Inter', sans-serif;
        }}

        .filter-btn:hover, .filter-btn.active {{
            background: rgba(245,197,24,0.15);
            border-color: var(--accent-gold);
            color: var(--accent-gold);
        }}

        .sort-select {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 10px 14px;
            color: var(--text-primary);
            font-size: 13px;
            font-family: 'Inter', sans-serif;
            outline: none;
            cursor: pointer;
        }}

        /* ─── Movie Table ─── */
        .section-title {{
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .section-title .count {{
            background: rgba(245,197,24,0.15);
            color: var(--accent-gold);
            font-size: 13px;
            padding: 4px 12px;
            border-radius: 100px;
            font-weight: 600;
        }}

        .table-wrapper {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            overflow: hidden;
            margin-bottom: 48px;
            box-shadow: var(--shadow-lg);
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
        }}

        thead th {{
            background: var(--bg-secondary);
            padding: 14px 16px;
            text-align: left;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-secondary);
            font-weight: 700;
            border-bottom: 1px solid var(--border);
            cursor: pointer;
            user-select: none;
            white-space: nowrap;
        }}

        thead th:hover {{
            color: var(--accent-gold);
        }}

        tbody tr {{
            border-bottom: 1px solid rgba(255,255,255,0.04);
            transition: background 0.2s;
        }}

        tbody tr:hover {{
            background: var(--bg-card-hover);
        }}

        tbody td {{
            padding: 14px 16px;
            font-size: 14px;
            vertical-align: middle;
        }}

        .title-cell {{
            display: flex;
            align-items: center;
            gap: 14px;
        }}

        .poster-thumb {{
            width: 40px;
            height: 56px;
            border-radius: 6px;
            object-fit: cover;
            background: var(--bg-secondary);
            flex-shrink: 0;
        }}

        .title-info h3 {{
            font-size: 14px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 2px;
        }}

        .title-info span {{
            font-size: 12px;
            color: var(--text-secondary);
        }}

        .rating-badge {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            background: rgba(245,197,24,0.12);
            color: var(--accent-gold);
            padding: 4px 10px;
            border-radius: 8px;
            font-weight: 700;
            font-size: 14px;
            white-space: nowrap;
        }}

        .rating-badge.high {{ background: rgba(34,197,94,0.12); color: var(--accent-green); }}
        .rating-badge.mid {{ background: rgba(245,197,24,0.12); color: var(--accent-gold); }}
        .rating-badge.low {{ background: rgba(239,68,68,0.12); color: var(--accent-red); }}

        .genre-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
        }}

        .genre-tag {{
            background: rgba(168,85,247,0.12);
            color: var(--accent-purple);
            padding: 2px 8px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 500;
            white-space: nowrap;
        }}

        .type-badge {{
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            padding: 3px 8px;
            border-radius: 6px;
            letter-spacing: 0.5px;
        }}

        .type-badge.movie {{ background: rgba(74,158,255,0.12); color: var(--accent-blue); }}
        .type-badge.series {{ background: rgba(168,85,247,0.12); color: var(--accent-purple); }}

        .file-name {{
            font-family: 'Courier New', monospace;
            font-size: 12px;
            color: var(--text-muted);
            max-width: 250px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}

        .imdb-link {{
            color: var(--accent-blue);
            text-decoration: none;
            font-size: 13px;
        }}

        .imdb-link:hover {{
            color: var(--accent-gold);
            text-decoration: underline;
        }}

        /* ─── Not Found Section ─── */
        .not-found-section {{
            background: rgba(239,68,68,0.05);
            border: 1px solid rgba(239,68,68,0.15);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 48px;
        }}

        .not-found-section h2 {{
            color: var(--accent-red);
            font-size: 18px;
            margin-bottom: 12px;
        }}

        .not-found-list {{
            list-style: none;
        }}

        .not-found-list li {{
            padding: 8px 0;
            border-bottom: 1px solid rgba(239,68,68,0.08);
            font-size: 13px;
            color: var(--text-secondary);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .not-found-list li:last-child {{
            border-bottom: none;
        }}

        /* ─── Footer ─── */
        .footer {{
            text-align: center;
            padding: 32px;
            color: var(--text-muted);
            font-size: 13px;
            border-top: 1px solid var(--border);
            margin-top: 48px;
        }}

        /* ─── Responsive ─── */
        @media (max-width: 768px) {{
            .controls {{ flex-direction: column; }}
            .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
            .table-wrapper {{ overflow-x: auto; }}
            table {{ min-width: 900px; }}
        }}

        /* ─── Animations ─── */
        @keyframes fadeInUp {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .stat-card, .table-wrapper, .not-found-section {{
            animation: fadeInUp 0.6s ease-out both;
        }}

        .stat-card:nth-child(2) {{ animation-delay: 0.1s; }}
        .stat-card:nth-child(3) {{ animation-delay: 0.2s; }}
        .stat-card:nth-child(4) {{ animation-delay: 0.3s; }}
        .stat-card:nth-child(5) {{ animation-delay: 0.4s; }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div class="header-badge">⭐ IMDb Data Report</div>
            <h1>Movie & Series Report</h1>
            <p>Auto-generated IMDb analysis of your media library</p>
            <div class="folder-path">📁 {folder_path}</div>
        </div>

        <!-- Stats -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{total}</div>
                <div class="stat-label">Total Files</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(found_results)}</div>
                <div class="stat-label">IMDb Matched</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(movies)}</div>
                <div class="stat-label">Movies</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(series)}</div>
                <div class="stat-label">Series</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">⭐ {avg_rating}</div>
                <div class="stat-label">Avg Rating</div>
            </div>
        </div>

        <!-- Controls -->
        <div class="controls">
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="Search by title, genre, director..." onkeyup="filterTable()">
            </div>
            <button class="filter-btn active" onclick="setFilter('all', this)">All</button>
            <button class="filter-btn" onclick="setFilter('movie', this)">🎬 Movies</button>
            <button class="filter-btn" onclick="setFilter('series', this)">📺 Series</button>
            <select class="sort-select" id="sortSelect" onchange="sortTable()">
                <option value="rating-desc">Sort: Rating ↓</option>
                <option value="rating-asc">Sort: Rating ↑</option>
                <option value="title-asc">Sort: Title A→Z</option>
                <option value="title-desc">Sort: Title Z→A</option>
                <option value="year-desc">Sort: Year ↓</option>
                <option value="year-asc">Sort: Year ↑</option>
            </select>
        </div>

        <!-- Results Table -->
        <div class="section-title">
            📋 Full Library <span class="count" id="resultCount">{len(found_results)} titles</span>
        </div>

        <div class="table-wrapper">
            <table id="resultsTable">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Title</th>
                        <th>Type</th>
                        <th>IMDb Rating</th>
                        <th>Year</th>
                        <th>Genre</th>
                        <th>Director</th>
                        <th>File</th>
                        <th>Link</th>
                    </tr>
                </thead>
                <tbody>
"""

    for idx, r in enumerate(sorted(found_results, key=lambda x: _safe_rating(x), reverse=True), 1):
        rating_val = _safe_rating(r)
        rating_class = 'high' if rating_val >= 7.5 else ('mid' if rating_val >= 5.5 else 'low')

        poster_html = ''
        if r.get('poster') and r['poster'] != 'N/A':
            poster_html = f'<img class="poster-thumb" src="{r["poster"]}" alt="" loading="lazy">'
        else:
            poster_html = '<div class="poster-thumb" style="display:flex;align-items:center;justify-content:center;font-size:18px;">🎬</div>'

        type_class = r.get('type', 'movie')
        type_label = r.get('type', 'N/A').capitalize()

        genres_html = ''
        if r.get('genre') and r['genre'] != 'N/A':
            for g in r['genre'].split(','):
                genres_html += f'<span class="genre-tag">{g.strip()}</span>'

        imdb_link = ''
        if r.get('imdb_id'):
            imdb_link = f'<a class="imdb-link" href="https://www.imdb.com/title/{r["imdb_id"]}/" target="_blank">IMDb ↗</a>'

        html += f"""                    <tr data-type="{type_class}" data-rating="{rating_val}" data-title="{r['title']}" data-year="{r.get('year', '')}" data-search="{r['title'].lower()} {r.get('genre','').lower()} {r.get('director','').lower()} {r.get('actors','').lower()}">
                        <td style="color:var(--text-muted);font-size:12px;">{idx}</td>
                        <td>
                            <div class="title-cell">
                                {poster_html}
                                <div class="title-info">
                                    <h3>{r['title']}</h3>
                                    <span>{r.get('runtime', 'N/A')} • {r.get('country', 'N/A')}</span>
                                </div>
                            </div>
                        </td>
                        <td><span class="type-badge {type_class}">{type_label}</span></td>
                        <td><span class="rating-badge {rating_class}">⭐ {r.get('imdb_rating', 'N/A')}</span></td>
                        <td style="white-space:nowrap;">{r.get('year', 'N/A')}</td>
                        <td><div class="genre-tags">{genres_html}</div></td>
                        <td style="font-size:13px;">{r.get('director', 'N/A')}</td>
                        <td><span class="file-name" title="{r.get('original_filename', '')}">{r.get('original_filename', '')}</span></td>
                        <td>{imdb_link}</td>
                    </tr>
"""

    html += """                </tbody>
            </table>
        </div>
"""

    # Not found section
    if not_found:
        html += f"""
        <div class="not-found-section">
            <h2>⚠️ Not Found on IMDb ({len(not_found)} files)</h2>
            <ul class="not-found-list">
"""
        for nf in not_found:
            html += f'                <li><span>{nf.get("original_filename", "")}</span><span style="color:var(--text-muted)">Searched: "{nf.get("title", "")}"</span></li>\n'
        html += """            </ul>
        </div>
"""

    # Top 10
    if rated_items:
        html += """
        <div class="section-title">🏆 Top 10 Highest Rated</div>
        <div class="stats-grid" style="grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); margin-bottom: 48px;">
"""
        for rating, r in rated_items[:10]:
            poster_src = r.get('poster', '') if r.get('poster') != 'N/A' else ''
            poster_bg = f'background-image: url({poster_src}); background-size: cover; background-position: center;' if poster_src else ''
            html += f"""            <div class="stat-card" style="text-align:left;padding:0;overflow:hidden;">
                <div style="height:6px; background: var(--gradient-gold);"></div>
                <div style="padding:18px;">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">
                        <div>
                            <div style="font-weight:700;font-size:15px;">{r['title']}</div>
                            <div style="font-size:12px;color:var(--text-secondary);">{r.get('year','')} • {r.get('type','').capitalize()}</div>
                        </div>
                        <span class="rating-badge high">⭐ {rating}</span>
                    </div>
                    <div style="font-size:12px;color:var(--text-muted);">{r.get('genre','N/A')}</div>
                </div>
            </div>
"""
        html += "        </div>\n"

    html += f"""
        <!-- Footer -->
        <div class="footer">
            Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')} — IMDb Report Generator
        </div>
    </div>

    <script>
        let currentFilter = 'all';

        function setFilter(type, btn) {{
            currentFilter = type;
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            filterTable();
        }}

        function filterTable() {{
            const search = document.getElementById('searchInput').value.toLowerCase();
            const rows = document.querySelectorAll('#resultsTable tbody tr');
            let visible = 0;
            
            rows.forEach(row => {{
                const matchType = currentFilter === 'all' || row.dataset.type === currentFilter;
                const matchSearch = !search || row.dataset.search.includes(search);
                
                if (matchType && matchSearch) {{
                    row.style.display = '';
                    visible++;
                }} else {{
                    row.style.display = 'none';
                }}
            }});
            
            document.getElementById('resultCount').textContent = visible + ' titles';
        }}

        function sortTable() {{
            const sortVal = document.getElementById('sortSelect').value;
            const tbody = document.querySelector('#resultsTable tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            
            rows.sort((a, b) => {{
                switch (sortVal) {{
                    case 'rating-desc': return (parseFloat(b.dataset.rating) || 0) - (parseFloat(a.dataset.rating) || 0);
                    case 'rating-asc': return (parseFloat(a.dataset.rating) || 0) - (parseFloat(b.dataset.rating) || 0);
                    case 'title-asc': return a.dataset.title.localeCompare(b.dataset.title);
                    case 'title-desc': return b.dataset.title.localeCompare(a.dataset.title);
                    case 'year-desc': return (b.dataset.year || '').localeCompare(a.dataset.year || '');
                    case 'year-asc': return (a.dataset.year || '').localeCompare(b.dataset.year || '');
                }}
            }});
            
            rows.forEach((row, i) => {{
                row.querySelector('td').textContent = i + 1;
                tbody.appendChild(row);
            }});
        }}
    </script>
</body>
</html>"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)


def _safe_rating(r):
    """Safely extract numeric rating."""
    try:
        return float(r.get('imdb_rating', 0))
    except (ValueError, TypeError):
        return 0


def generate_rename_batch(results, folder_path, output_path):
    """Generate a batch file to rename video files with IMDb rating prefix."""
    lines = [
        '@echo off',
        'chcp 65001 >nul',
        'echo ════════════════════════════════════════════════════',
        'echo    IMDb Rating Renamer',
        'echo    This will prepend IMDb ratings to filenames',
        'echo ════════════════════════════════════════════════════',
        'echo.',
        'echo WARNING: This will rename your video files!',
        'echo Press Ctrl+C to cancel, or...',
        'pause',
        'echo.',
        '',
    ]

    rename_count = 0
    for r in results:
        if not r.get('found'):
            continue

        rating = r.get('imdb_rating', 'N/A')
        if rating == 'N/A':
            continue

        original_filename = r.get('original_filename', '')
        filepath = r.get('filepath', '')
        if not original_filename or not filepath:
            continue

        # Skip if already has a rating prefix
        if re.match(r'^\d+\.\d+_', original_filename):
            continue

        file_dir = os.path.dirname(filepath)
        name_no_ext = os.path.splitext(original_filename)[0]
        ext = os.path.splitext(original_filename)[1]

        # Clean the name: replace spaces with underscores, lowercase
        clean_name = re.sub(r'[^\w\-.]', '_', name_no_ext)
        clean_name = re.sub(r'_+', '_', clean_name).strip('_').lower()

        new_filename = f"{rating}_{clean_name}{ext}"

        # Use the full path for the rename
        old_path = filepath.replace('/', '\\')
        new_path = os.path.join(file_dir, new_filename).replace('/', '\\')

        lines.append(f'echo Renaming: "{original_filename}"')
        lines.append(f'echo      To: "{new_filename}"')
        lines.append(f'ren "{old_path}" "{new_filename}"')
        lines.append(f'if %errorlevel% equ 0 (echo    [OK]) else (echo    [FAILED])')
        lines.append('')
        rename_count += 1

    if rename_count == 0:
        lines.append('echo No files to rename (no valid ratings found or all files already have ratings).')
    else:
        lines.append(f'echo.')
        lines.append(f'echo ════════════════════════════════════════════════════')
        lines.append(f'echo    Done! Renamed {rename_count} file(s).')
        lines.append(f'echo ════════════════════════════════════════════════════')

    lines.append('echo.')
    lines.append('pause')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


# ─── GUI Helpers ────────────────────────────────────────────────────────────────

def create_progress_window():
    """Create a progress/status window."""
    win = tk.Tk()
    win.title("IMDb Report Generator")
    win.geometry("550x400")
    win.configure(bg='#1a1a2e')
    win.resizable(False, False)

    # Center the window
    win.update_idletasks()
    x = (win.winfo_screenwidth() // 2) - 275
    y = (win.winfo_screenheight() // 2) - 200
    win.geometry(f'+{x}+{y}')

    # Title
    title_lbl = tk.Label(win, text="⭐ IMDb Report Generator", font=('Segoe UI', 16, 'bold'),
                         fg='#f5c518', bg='#1a1a2e')
    title_lbl.pack(pady=(20, 5))

    subtitle_lbl = tk.Label(win, text="Fetching data from OMDb API...", font=('Segoe UI', 10),
                            fg='#9898b0', bg='#1a1a2e')
    subtitle_lbl.pack(pady=(0, 15))

    # Progress
    progress_var = tk.StringVar(value="Starting...")
    progress_lbl = tk.Label(win, textvariable=progress_var, font=('Segoe UI', 10, 'bold'),
                            fg='#4a9eff', bg='#1a1a2e')
    progress_lbl.pack(pady=(0, 10))

    # Status text area
    frame = tk.Frame(win, bg='#12121a', bd=1, relief='solid')
    frame.pack(padx=20, pady=(0, 20), fill='both', expand=True)

    log_text = tk.Text(frame, font=('Consolas', 9), bg='#12121a', fg='#e8e8f0',
                       insertbackground='#f5c518', relief='flat', padx=10, pady=10,
                       state='disabled', wrap='word')
    log_text.pack(fill='both', expand=True)

    # Tag configs for colored output
    log_text.tag_configure('success', foreground='#22c55e')
    log_text.tag_configure('error', foreground='#ef4444')
    log_text.tag_configure('info', foreground='#4a9eff')
    log_text.tag_configure('warn', foreground='#f5c518')

    return win, progress_var, log_text


def log_message(log_text, message, tag=None):
    """Append a message to the log text widget."""
    log_text.configure(state='normal')
    if tag:
        log_text.insert('end', message + '\n', tag)
    else:
        log_text.insert('end', message + '\n')
    log_text.see('end')
    log_text.configure(state='disabled')
    log_text.update()


# ─── Main ───────────────────────────────────────────────────────────────────────

def main():
    # Hide root for dialogs
    root = tk.Tk()
    root.withdraw()

    # ── Load/Get API Key ──
    config = load_config()
    api_key = config.get('api_key', '')

    if not api_key:
        messagebox.showinfo(
            "OMDb API Key Required",
            "You need a free OMDb API key to fetch IMDb data.\n\n"
            "Get one at: https://www.omdbapi.com/apikey.aspx\n"
            "(Free tier: 1,000 requests/day)\n\n"
            "Enter your API key in the next dialog."
        )
        api_key = simpledialog.askstring("API Key", "Enter your OMDb API key:", parent=root)
        if not api_key:
            messagebox.showerror("Error", "No API key provided. Exiting.")
            sys.exit(1)
        config['api_key'] = api_key.strip()
        save_config(config)

    # ── Select Folder ──
    folder = filedialog.askdirectory(
        title="Select folder containing movies / web series",
        initialdir=os.path.expanduser("~\\Desktop")
    )

    if not folder:
        messagebox.showinfo("Cancelled", "No folder selected. Exiting.")
        sys.exit(0)

    root.destroy()

    # ── Scan Videos ──
    print(f"Scanning: {folder}")
    videos = scan_video_files(folder)

    if not videos:
        root2 = tk.Tk()
        root2.withdraw()
        messagebox.showinfo("No Videos Found", f"No video files found in:\n{folder}")
        sys.exit(0)

    # ── Create Progress Window ──
    win, progress_var, log_text = create_progress_window()
    win.update()

    log_message(log_text, f"📁 Folder: {folder}", 'info')
    log_message(log_text, f"🎬 Found {len(videos)} video file(s)", 'info')
    log_message(log_text, "─" * 50)

    # ── Deduplicate: group by cleaned title ──
    title_map = {}  # cleaned_title -> list of video_info
    for v in videos:
        clean = clean_filename(v['filename'])
        year = extract_year(v['filename'])
        key = (clean.lower(), year)
        if key not in title_map:
            title_map[key] = {
                'clean_title': clean,
                'year': year,
                'is_series': is_likely_series(v['filename']),
                'files': []
            }
        title_map[key]['files'].append(v)

    log_message(log_text, f"📋 {len(title_map)} unique title(s) to look up", 'info')
    log_message(log_text, "─" * 50)

    # ── Load Cache ──
    cache = load_cache()

    # ── Fetch IMDb Data ──
    all_results = []
    total_titles = len(title_map)

    for idx, ((title_key, year_key), title_info) in enumerate(title_map.items(), 1):
        clean_title = title_info['clean_title']
        year = title_info['year']
        is_series = title_info['is_series']

        progress_var.set(f"Looking up {idx}/{total_titles}...")
        win.update()

        # Check cache
        cache_key = f"{clean_title.lower()}|{year or ''}|{'series' if is_series else 'movie'}"
        if cache_key in cache:
            data = cache[cache_key]
            log_message(log_text, f"  ✓ [CACHE] {clean_title} → {data.get('title', '?')} ({data.get('imdb_rating', 'N/A')})", 'success')
        else:
            # Fetch from API
            media_type = 'series' if is_series else None
            data = fetch_imdb_data(clean_title, api_key, year=year, media_type=media_type)

            # If not found as series, try as movie (and vice versa)
            if not data.get('found') and is_series:
                data = fetch_imdb_data(clean_title, api_key, year=year, media_type='movie')
            elif not data.get('found') and not is_series:
                data = fetch_imdb_data(clean_title, api_key, year=year, media_type='series')

            # Try without year if still not found
            if not data.get('found') and year:
                data = fetch_imdb_data(clean_title, api_key, year=None, media_type=None)

            cache[cache_key] = data
            time.sleep(0.3)  # Rate limit: ~3 requests/sec

            if data.get('found'):
                log_message(log_text, f"  ✓ {clean_title} → {data.get('title', '?')} ⭐ {data.get('imdb_rating', 'N/A')}", 'success')
            else:
                log_message(log_text, f"  ✗ {clean_title} — {data.get('error', 'Not found')}", 'error')

        # Attach to each file
        for fv in title_info['files']:
            result = dict(data)
            result['original_filename'] = fv['filename']
            result['filepath'] = fv['filepath']
            result['size_mb'] = fv['size_mb']
            all_results.append(result)

    # ── Save Cache ──
    save_cache(cache)

    # ── Generate Outputs ──
    progress_var.set("Generating report...")
    win.update()

    report_path = os.path.join(SCRIPT_DIR, "imdb_report.html")
    batch_path = os.path.join(SCRIPT_DIR, "rename_with_ratings.bat")

    generate_html_report(all_results, folder, report_path)
    generate_rename_batch(all_results, folder, batch_path)

    log_message(log_text, "─" * 50)
    log_message(log_text, f"📄 Report: {report_path}", 'success')
    log_message(log_text, f"📝 Batch:  {batch_path}", 'success')
    log_message(log_text, "")

    found_count = sum(1 for r in all_results if r.get('found'))
    log_message(log_text, f"✅ Done! {found_count}/{len(all_results)} files matched on IMDb.", 'warn')

    progress_var.set("✅ Complete!")

    # Open report in browser
    try:
        import webbrowser
        webbrowser.open(report_path)
    except Exception:
        pass

    # Change button to exit
    exit_btn = tk.Button(win, text="Close", font=('Segoe UI', 11, 'bold'),
                         bg='#f5c518', fg='#0a0a0f', relief='flat',
                         padx=30, pady=8, cursor='hand2',
                         command=win.destroy)
    exit_btn.pack(pady=(0, 15))

    win.mainloop()


if __name__ == "__main__":
    main()
