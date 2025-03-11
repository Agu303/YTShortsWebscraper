"""
YouTube Shorts Analyzer
----------------------

This script analyzes YouTube Shorts videos and provides engagement metrics.

Setup Instructions:
1. Install required packages:
   pip install google-api-python-client python-dotenv pandas

2. Get a YouTube API Key:
   a. Go to https://console.cloud.google.com/
   b. Create a new project
   c. Enable the YouTube Data API v3
   d. Create credentials (API key)

3. Set up your API key in one of these ways:
   - Create a 'webap.env' file with: YOUTUBE_API_KEY=your_key_here
   - Set environment variable: YOUTUBE_API_KEY=your_key_here
   - Pass the key directly when running the script

Usage:
  python youtube_shorts_analyzer.py [--api_key YOUR_API_KEY]
"""

import os
import pandas as pd
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from dotenv import load_dotenv
import time
import logging
from typing import List, Dict, Optional, Any
from googleapiclient.errors import HttpError
import backoff
import math
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get the directory where the script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Available sorting methods and categories
SORT_OPTIONS = {
    '1': 'viewCount',
    '2': 'rating',
    '3': 'relevance',
    '4': 'date'
}

SHORTS_CATEGORIES = {
    '1': 'trending shorts',
    '2': 'gaming shorts',
    '3': 'music shorts',
    '4': 'comedy shorts',
    '5': 'dance shorts',
    '6': 'tutorial shorts',
    '7': 'challenge shorts',
    '8': 'viral shorts'
}

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='YouTube Shorts Analyzer')
    parser.add_argument('--api_key', type=str, help='YouTube API key (optional if set in env file or environment)')
    return parser.parse_args()

def check_environment_setup(api_key: Optional[str] = None) -> str:
    """
    Check if all required files and environment variables are set up correctly.
    
    Args:
        api_key: Optional API key provided via command line
    
    Returns:
        str: Valid YouTube API key
    """
    if api_key:
        logger.info("Using API key provided via command line")
        return api_key
        
    # Try to load from environment variable first
    api_key = os.getenv('YOUTUBE_API_KEY')
    if api_key:
        logger.info("Using API key from environment variable")
        return api_key
    
    # Try to load from .env file
    env_files = ['webap.env', '.env']
    for env_file in env_files:
        env_path = os.path.join(os.path.dirname(__file__), env_file)
        if os.path.exists(env_path):
            load_dotenv(env_path)
            api_key = os.getenv('YOUTUBE_API_KEY')
            if api_key:
                logger.info(f"Using API key from {env_file}")
                return api_key
    
    # If we get here, no API key was found
    raise ValueError(
        "YouTube API key not found. Please either:\n"
        "1. Create a 'webap.env' file with: YOUTUBE_API_KEY=your_key_here\n"
        "2. Set environment variable: YOUTUBE_API_KEY=your_key_here\n"
        "3. Pass the key directly: python youtube_shorts_analyzer.py --api_key YOUR_KEY"
    )

def create_output_directory():
    """Create output directory for CSV files if it doesn't exist."""
    output_dir = os.path.join(SCRIPT_DIR, 'output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir

def get_user_preferences():
    """Get user preferences for the YouTube Shorts search."""
    print("\n=== YouTube Shorts Analyzer Settings ===")
    
    # Get sorting method
    print("\nAvailable sorting methods:")
    for key, value in SORT_OPTIONS.items():
        print(f"{key}. {value}")
    while True:
        sort_choice = input("\nChoose sorting method (1-4): ")
        if sort_choice in SORT_OPTIONS:
            break
        print("Invalid choice. Please try again.")
    
    # Get category
    print("\nAvailable categories:")
    for key, value in SHORTS_CATEGORIES.items():
        print(f"{key}. {value}")
    while True:
        category_choice = input("\nChoose category (1-8): ")
        if category_choice in SHORTS_CATEGORIES:
            break
        print("Invalid choice. Please try again.")
    
    # Get number of videos
    while True:
        try:
            max_results = int(input("\nHow many videos to analyze (1-50)? "))
            if 1 <= max_results <= 50:
                break
            print("Please enter a number between 1 and 50.")
        except ValueError:
            print("Please enter a valid number.")
    
    # Get date range
    print("\nEnter the date range to search (format: YYYY-MM-DD)")
    while True:
        try:
            start_date_str = input("Start date: ")
            end_date_str = input("End date: ")
            
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            
            if start_date > end_date:
                print("Start date must be before end date.")
                continue
                
            if end_date > datetime.now():
                print("End date cannot be in the future.")
                continue
                
            # Convert to UTC ISO format
            start_date = start_date.isoformat() + "Z"
            end_date = end_date.isoformat() + "Z"
            break
            
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD (e.g., 2024-03-20)")
    
    return {
        'sort_method': SORT_OPTIONS[sort_choice],
        'category': SHORTS_CATEGORIES[category_choice],
        'max_results': max_results,
        'start_date': start_date,
        'end_date': end_date
    }

class YouTubeShortsAnalyzer:
    """A class to analyze YouTube Shorts videos using the YouTube Data API."""
    
    # Quota costs for different API operations
    QUOTA_COSTS = {
        'search': 100,  # Cost per search request
        'video': 1,     # Cost per video details request
        'transcript': 0 # Transcript API doesn't count towards quota
    }
    
    def __init__(self, preferences: Dict[str, Any]):
        """Initialize the YouTube Shorts Analyzer."""
        logger.info("Initializing YouTubeShortsAnalyzer...")
        try:
            self.youtube = build('youtube', 'v3', developerKey=API_KEY)
            logger.info("Successfully initialized YouTube API client")
        except Exception as e:
            logger.error(f"Failed to initialize YouTube API client: {str(e)}")
            raise
            
        self.quota_used = 0
        self.max_quota = 10000  # Daily quota limit
        self.preferences = preferences

    def analyze_shorts(self):
        """Analyze YouTube Shorts videos."""
        try:
            # Use the date range from user preferences
            search_response = self.youtube.search().list(
                q=f"{self.preferences['category']}",
                type="video",
                videoDuration="short",
                part="id,snippet",
                maxResults=self.preferences['max_results'],
                order=self.preferences['sort_method'],
                publishedAfter=self.preferences['start_date'],
                publishedBefore=self.preferences['end_date'],
                regionCode="US",
                relevanceLanguage="en"
            ).execute()
            
            self.quota_used += self.QUOTA_COSTS['search']
            
            shorts_data = []
            seen_channels = set()  # Track channels to avoid duplicates
            
            for item in search_response.get('items', []):
                video_id = item['id']['videoId']
                channel_id = item['snippet']['channelId']
                
                # Skip if we already have content from this channel
                if channel_id in seen_channels:
                    continue
                    
                seen_channels.add(channel_id)
                
                # Get detailed video information
                video_response = self.youtube.videos().list(
                    part="snippet,statistics,contentDetails",
                    id=video_id
                ).execute()
                
                self.quota_used += self.QUOTA_COSTS['video']
                
                if video_response['items']:
                    video_info = video_response['items'][0]
                    
                    # Extract base metrics
                    view_count = int(video_info['statistics'].get('viewCount', 0))
                    like_count = int(video_info['statistics'].get('likeCount', 0))
                    comment_count = int(video_info['statistics'].get('commentCount', 0))
                    published_at = video_info['snippet']['publishedAt']
                    
                    # Calculate engagement metrics
                    engagement_metrics = self.calculate_engagement_metrics(
                        view_count=view_count,
                        like_count=like_count,
                        comment_count=comment_count,
                        published_at=published_at
                    )
                    
                    # Combine base data with engagement metrics
                    video_data = {
                        'video_id': video_id,
                        'title': video_info['snippet']['title'],
                        'channel_title': video_info['snippet']['channelTitle'],
                        'channel_id': channel_id,
                        'view_count': view_count,
                        'like_count': like_count,
                        'comment_count': comment_count,
                        'published_at': published_at,
                        'duration': video_info['contentDetails']['duration'],
                        'category': self.preferences['category'],
                        'sort_method': self.preferences['sort_method'],
                        # Add engagement metrics
                        'engagement_rate': engagement_metrics['engagement_rate'],
                        'likes_to_views_ratio': engagement_metrics['likes_to_views_ratio'],
                        'comments_to_views_ratio': engagement_metrics['comments_to_views_ratio'],
                        'avg_views_per_hour': engagement_metrics['avg_views_per_hour'],
                        'total_engagement': engagement_metrics['total_engagement'],
                        'performance_score': engagement_metrics['performance_score']
                    }
                    
                    shorts_data.append(video_data)
                    
                # Check if we're approaching quota limit
                if self.quota_used >= self.max_quota:
                    logger.warning("Approaching API quota limit. Stopping analysis.")
                    break
            
            # Sort data by performance score
            if shorts_data:
                shorts_data.sort(key=lambda x: x['performance_score'], reverse=True)
            
            return shorts_data
            
        except HttpError as e:
            logger.error(f"An API error occurred: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred: {str(e)}")
            return None

    def calculate_engagement_metrics(self, view_count: int, like_count: int, 
                                  comment_count: int, published_at: str) -> Dict[str, float]:
        """
        Calculate various engagement metrics for a video.
        
        Args:
            view_count: Number of views
            like_count: Number of likes
            comment_count: Number of comments
            published_at: Publication date in ISO format
        
        Returns:
            Dictionary containing calculated engagement metrics
        """
        # Prevent division by zero
        if view_count == 0:
            return {
                'engagement_rate': 0.0,
                'likes_to_views_ratio': 0.0,
                'comments_to_views_ratio': 0.0,
                'avg_views_per_hour': 0.0,
                'total_engagement': 0,
                'performance_score': 0.0
            }
        
        # Calculate time since publication
        pub_date = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
        time_since_pub = datetime.utcnow() - pub_date
        hours_since_pub = max(time_since_pub.total_seconds() / 3600, 1)  # Avoid division by zero
        
        # Calculate metrics
        total_engagement = like_count + comment_count
        engagement_rate = (total_engagement / view_count) * 100
        likes_to_views_ratio = (like_count / view_count) * 100
        comments_to_views_ratio = (comment_count / view_count) * 100
        avg_views_per_hour = view_count / hours_since_pub
        
        # Calculate performance score (weighted average of different metrics)
        weights = {
            'views': 0.4,
            'engagement': 0.3,
            'velocity': 0.3
        }
        
        # Normalize metrics for scoring (using log scale for views to handle viral videos better)
        normalized_views = min(math.log10(view_count + 1) / 8, 1)  # log10(100M) ≈ 8
        normalized_engagement = min(engagement_rate / 20, 1)  # Cap at 20% engagement rate
        normalized_velocity = min(avg_views_per_hour / 10000, 1)  # Cap at 10K views/hour
        
        performance_score = (
            weights['views'] * normalized_views +
            weights['engagement'] * normalized_engagement +
            weights['velocity'] * normalized_velocity
        ) * 100
        
        return {
            'engagement_rate': round(engagement_rate, 2),
            'likes_to_views_ratio': round(likes_to_views_ratio, 2),
            'comments_to_views_ratio': round(comments_to_views_ratio, 2),
            'avg_views_per_hour': round(avg_views_per_hour, 2),
            'total_engagement': total_engagement,
            'performance_score': round(performance_score, 2)
        }

    def save_to_csv(self, data, filename):
        """Save the analysis results to a CSV file."""
        try:
            df = pd.DataFrame(data)
            
            # Reorder columns for better readability
            column_order = [
                'video_id', 'title', 'channel_title', 'channel_id',
                'performance_score', 'view_count', 'like_count', 'comment_count',
                'engagement_rate', 'likes_to_views_ratio', 'comments_to_views_ratio',
                'avg_views_per_hour', 'total_engagement',
                'published_at', 'duration', 'category', 'sort_method'
            ]
            
            df = df[column_order]
            
            # Create output directory and save file
            output_dir = create_output_directory()
            file_path = os.path.join(output_dir, filename)
            df.to_csv(file_path, index=False)
            
            # Log summary statistics
            logger.info("\nSummary Statistics:")
            logger.info(f"Average Performance Score: {df['performance_score'].mean():.2f}")
            logger.info(f"Average Engagement Rate: {df['engagement_rate'].mean():.2f}%")
            logger.info(f"Total Views Analyzed: {df['view_count'].sum():,}")
            logger.info(f"Data saved to: {file_path}")
            
            # Create a simple HTML report
            self._create_html_report(df, output_dir, filename)
            
        except Exception as e:
            logger.error(f"Error saving data to CSV: {str(e)}")

    def _create_html_report(self, df: pd.DataFrame, output_dir: str, csv_filename: str):
        """Create a simple HTML report with the analysis results."""
        try:
            html_content = f"""
            <html>
            <head>
                <title>YouTube Shorts Analysis Report</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .summary {{ background-color: #f5f5f5; padding: 20px; border-radius: 5px; }}
                    table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #4CAF50; color: white; }}
                    tr:nth-child(even) {{ background-color: #f2f2f2; }}
                </style>
            </head>
            <body>
                <h1>YouTube Shorts Analysis Report</h1>
                <div class="summary">
                    <h2>Summary Statistics</h2>
                    <p>Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>Total Videos Analyzed: {len(df)}</p>
                    <p>Average Performance Score: {df['performance_score'].mean():.2f}</p>
                    <p>Average Engagement Rate: {df['engagement_rate'].mean():.2f}%</p>
                    <p>Total Views: {df['view_count'].sum():,}</p>
                </div>
                <h2>Top 10 Performing Shorts</h2>
                {df.nlargest(10, 'performance_score')[['title', 'channel_title', 'performance_score', 'view_count', 'engagement_rate']].to_html()}
            </body>
            </html>
            """
            
            html_filename = csv_filename.replace('.csv', '_report.html')
            html_path = os.path.join(output_dir, html_filename)
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            logger.info(f"HTML report generated: {html_path}")
            
        except Exception as e:
            logger.error(f"Error creating HTML report: {str(e)}")

def main():
    """Main entry point for the YouTube Shorts analyzer."""
    try:
        # Parse command line arguments
        args = parse_args()
        
        # Get API key and validate environment
        api_key = check_environment_setup(args.api_key)
        
        # Set the API key for use in the YouTubeShortsAnalyzer class
        global API_KEY
        API_KEY = api_key
        
        # Get user preferences
        preferences = get_user_preferences()
        
        # Initialize the analyzer with user preferences
        analyzer = YouTubeShortsAnalyzer(preferences)
        logger.info(f"Starting YouTube Shorts analysis from {preferences['start_date']} to {preferences['end_date']}")
        logger.info(f"Category: {preferences['category']}")
        logger.info(f"Sorting by: {preferences['sort_method']}")
        
        shorts_data = analyzer.analyze_shorts()
        
        if shorts_data:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'youtube_shorts_analysis_{timestamp}.csv'
            analyzer.save_to_csv(shorts_data, filename)
            logger.info(f"Analysis completed successfully. Processed {len(shorts_data)} unique shorts.")
        else:
            logger.warning("No shorts data was collected.")
            
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main()