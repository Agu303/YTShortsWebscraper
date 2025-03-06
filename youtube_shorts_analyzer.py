import os
import pandas as pd
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

class YouTubeShortsAnalyzer:
    def __init__(self):
        self.api_key = os.getenv('YOUTUBE_API_KEY')
        if not self.api_key:
            raise ValueError("Please set YOUTUBE_API_KEY in your .env file")
        
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)
        
    def get_popular_shorts(self, max_results=50):
        """Fetch popular YouTube Shorts"""
        try:
            # Get videos from the last 7 days
            published_after = (datetime.utcnow() - timedelta(days=7)).isoformat() + 'Z'
            
            request = self.youtube.search().list(
                part='snippet',
                type='video',
                videoDuration='short',
                order='viewCount',
                publishedAfter=published_after,
                maxResults=max_results
            )
            
            response = request.execute()
            return response['items']
        except Exception as e:
            print(f"Error fetching shorts: {str(e)}")
            return []

    def get_video_statistics(self, video_id):
        """Get detailed statistics for a video"""
        try:
            request = self.youtube.videos().list(
                part='statistics,contentDetails',
                id=video_id
            )
            response = request.execute()
            if response['items']:
                return response['items'][0]
            return None
        except Exception as e:
            print(f"Error fetching video statistics: {str(e)}")
            return None

    def get_video_transcript(self, video_id):
        """Get transcript for a video if available"""
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            return ' '.join([entry['text'] for entry in transcript])
        except Exception as e:
            print(f"Error fetching transcript: {str(e)}")
            return None

    def analyze_shorts(self):
        """Main method to analyze YouTube Shorts"""
        shorts_data = []
        shorts = self.get_popular_shorts()
        
        for short in shorts:
            video_id = short['id']['videoId']
            stats = self.get_video_statistics(video_id)
            
            if not stats:
                continue
                
            # Get transcript
            transcript = self.get_video_transcript(video_id)
            
            # Extract relevant data
            short_data = {
                'video_id': video_id,
                'title': short['snippet']['title'],
                'channel_title': short['snippet']['channelTitle'],
                'published_at': short['snippet']['publishedAt'],
                'views': stats['statistics'].get('viewCount', 0),
                'likes': stats['statistics'].get('likeCount', 0),
                'comments': stats['statistics'].get('commentCount', 0),
                'duration': stats['contentDetails']['duration'],
                'transcript': transcript if transcript else '',
                'description': short['snippet']['description']
            }
            
            shorts_data.append(short_data)
            time.sleep(1)  # Rate limiting to avoid API quota issues
            
        return shorts_data

    def save_to_csv(self, data, filename='youtube_shorts_analysis.csv'):
        """Save the analysis results to a CSV file"""
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")

def main():
    try:
        analyzer = YouTubeShortsAnalyzer()
        print("Starting YouTube Shorts analysis...")
        shorts_data = analyzer.analyze_shorts()
        
        if shorts_data:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'youtube_shorts_analysis_{timestamp}.csv'
            analyzer.save_to_csv(shorts_data, filename)
            print(f"Analysis completed successfully. Processed {len(shorts_data)} shorts.")
        else:
            print("No shorts data was collected.")
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 