"""
Test Google Geolocation API
Run this to verify your API key is working correctly
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_google_geolocation():
    """Test Google Geolocation API"""
    
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    
    if not api_key or api_key == 'your-google-maps-api-key':
        print("❌ Google Maps API key not configured in .env file")
        return False
    
    print(f"🔑 API Key found: {api_key[:20]}...")
    
    # Test API call
    url = f"https://www.googleapis.com/geolocation/v1/geolocate?key={api_key}"
    
    try:
        print("📡 Testing Google Geolocation API...")
        response = requests.post(
            url,
            json={"considerIp": True},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API is working!")
            print(f"📍 Location: {data['location']['lat']}, {data['location']['lng']}")
            print(f"🎯 Accuracy: ±{data['accuracy']}m")
            return True
        elif response.status_code == 403:
            print("❌ API key is invalid or restricted")
            print("💡 Check:")
            print("   1. API key is correct")
            print("   2. Geolocation API is enabled in Google Cloud Console")
            print("   3. API key restrictions allow your domain")
            return False
        else:
            print(f"❌ API error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Google Geolocation API Test")
    print("=" * 60)
    
    success = test_google_geolocation()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Setup Complete! Your API is ready to use.")
        print("\n💡 Next steps:")
        print("   1. Restart your Flask application")
        print("   2. Try creating a lecture with 'High Accuracy Mode'")
        print("   3. You should see 'WiFi Positioning' in the results")
    else:
        print("❌ Setup needs attention. See errors above.")
        print("\n💡 Troubleshooting:")
        print("   1. Check GOOGLE_MAPS_SETUP.md for setup instructions")
        print("   2. Verify API key in .env file")
        print("   3. Enable Geolocation API in Google Cloud Console")
    print("=" * 60)
