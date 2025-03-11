# YouTube Shorts Analyzer

This Python script analyzes YouTube Shorts using the YouTube Data API. It collects various metrics including views, likes, comments, and provides detailed engagement analytics with performance scoring.

## Features

- Fetch YouTube Shorts based on user-selected categories and sorting methods
- Collect comprehensive engagement metrics:
  - View count, likes, and comments
  - Engagement rate
  - Likes-to-views ratio
  - Comments-to-views ratio
  - Average views per hour
  - Performance score based on weighted metrics
- Customizable date range for analysis
- Generates both CSV and HTML reports
- Includes error handling and API quota management
- Prevents duplicate channel analysis for better diversity
- Supports multiple sorting methods:
  - View count
  - Rating
  - Relevance
  - Date
- Multiple category options:
  - Trending shorts
  - Gaming shorts
  - Music shorts
  - Comedy shorts
  - Dance shorts
  - Tutorial shorts
  - Challenge shorts
  - Viral shorts

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
3. Set up your YouTube API key in one of these ways:
   - Create a `webap.env` or `.env` file with:
     ```
     YOUTUBE_API_KEY=your_api_key_here
     ```
   - Set as environment variable:
     ```
     YOUTUBE_API_KEY=your_api_key_here
     ```
   - Pass directly when running the script:
     ```
     python youtube_shorts_analyzer.py --api_key YOUR_API_KEY
     ```

## Getting a YouTube API Key

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the YouTube Data API v3
4. Create credentials (API key)
5. Copy the API key to use with the script

## Usage

Run the script:
```bash
python youtube_shorts_analyzer.py
```

The script will prompt you to:
1. Choose a sorting method (viewCount, rating, relevance, or date)
2. Select a category of shorts to analyze
3. Specify the number of videos to analyze (1-50)
4. Enter a date range for the search

## Output

The script generates two types of output files in the `output` directory:

### CSV File
Contains detailed metrics for each analyzed Short:
- Video ID and Title
- Channel Information
- View, Like, and Comment Counts
- Engagement Metrics
- Performance Scores
- Publication Date and Duration

### HTML Report
Provides a user-friendly visualization including:
- Summary Statistics
- Analysis Date
- Total Videos Analyzed
- Average Performance Score
- Average Engagement Rate
- Total Views
- Top 10 Performing Shorts Table

## Notes

- The script includes quota management to avoid API limits
- Daily YouTube API quota limits apply
- Performance scores are calculated using weighted averages of views, engagement, and velocity
- Duplicate channels are filtered to ensure content diversity
- The script processes English language content by default
- All times are in UTC 