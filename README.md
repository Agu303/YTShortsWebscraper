# YouTube Shorts Analyzer

This Python script analyzes popular YouTube Shorts using the YouTube Data API and YouTube Transcript API. It collects various metrics including views, likes, comments, and transcripts, then saves the data to CSV files.

## Features

- Fetches popular YouTube Shorts from the last 7 days
- Collects engagement metrics (views, likes, comments)
- Retrieves video transcripts where available
- Saves data to timestamped CSV files
- Includes error handling and rate limiting

## Prerequisites

- Python 3.7 or higher
- YouTube Data API key
- Required Python packages (listed in requirements.txt)

## Setup

1. Clone this repository or download the files
2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project root and add your YouTube API key:
   ```
   YOUTUBE_API_KEY=your_api_key_here
   ```

## Getting a YouTube API Key

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the YouTube Data API v3
4. Create credentials (API key)
5. Copy the API key to your `.env` file

## Usage

Run the script:
```bash
python youtube_shorts_analyzer.py
```

The script will:
1. Fetch popular Shorts from the last 7 days
2. Collect engagement metrics and transcripts
3. Save the data to a CSV file with timestamp in the filename

## Output

The script generates a CSV file containing the following information for each Short:
- Video ID
- Title
- Channel Title
- Publication Date
- View Count
- Like Count
- Comment Count
- Duration
- Transcript (if available)
- Description

## Notes

- The script includes rate limiting to avoid API quota issues
- Some videos may not have transcripts available
- The YouTube Data API has daily quota limits
- The script processes up to 50 Shorts by default (configurable in the code) 