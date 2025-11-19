# Google Maps API Setup Guide

## Why Do We Need This?

The Google Maps Geolocation API helps improve location accuracy, especially indoors, by using WiFi and cell tower positioning. This gives you **Zomato/Uber-level accuracy** even when GPS signals are weak.

## Benefits:

- **Indoor Accuracy**: ±10-50m (vs ±100-1000m with GPS alone)
- **Faster Lock**: 2-5 seconds (vs 30-60 seconds for GPS)
- **More Reliable**: Works in buildings, basements, etc.
- **Free Tier**: 40,000 requests/month (plenty for most schools)

---

## Step-by-Step Setup (5 minutes):

### 1. Go to Google Cloud Console
Visit: https://console.cloud.google.com/

### 2. Create a New Project (or use existing)
- Click "Select a project" at the top
- Click "NEW PROJECT"
- Name it: "Geo Attendance Pro"
- Click "CREATE"

### 3. Enable the Geolocation API
- Go to: https://console.cloud.google.com/apis/library
- Search for "Geolocation API"
- Click on it
- Click "ENABLE"

### 4. Create API Credentials
- Go to: https://console.cloud.google.com/apis/credentials
- Click "CREATE CREDENTIALS"
- Select "API key"
- Copy the API key (looks like: `AIzaSyD...`)

### 5. Restrict the API Key (Important for Security)
- Click on the API key you just created
- Under "API restrictions":
  - Select "Restrict key"
  - Check "Geolocation API"
- Under "Application restrictions":
  - Select "HTTP referrers (web sites)"
  - Add your domain: `yourdomain.com/*`
  - For development, add: `localhost:5000/*` and `127.0.0.1:5000/*`
- Click "SAVE"

### 6. Add to Your .env File
```bash
GOOGLE_MAPS_API_KEY=AIzaSyD...your-actual-key-here
```

### 7. Restart Your Application
```bash
# Stop the app (Ctrl+C)
# Start it again
python run.py
```

---

## Pricing (Don't Worry, It's Free!)

### Free Tier:
- **40,000 requests/month** = FREE
- That's ~1,300 requests per day
- Enough for 100+ teachers creating lectures daily

### Typical Usage:
- Teacher creates lecture: 1-3 requests
- Student checks in: 0 requests (uses browser GPS)
- **You'll likely stay within free tier**

### If You Exceed Free Tier:
- $5 per 1,000 additional requests
- You can set spending limits to $0 to prevent charges

---

## Testing the Setup:

### 1. Check if API Key is Loaded:
Open browser console (F12) and check for:
```
🎯 Starting hybrid location system...
📶 Trying Google WiFi positioning...
```

### 2. Test Location Accuracy:
- Create a new lecture
- Click "High Accuracy Mode"
- You should see: "✅ High accuracy location captured! ±15m (WiFi Positioning)"

### 3. If It's Not Working:
- Check API key is in `.env` file
- Restart the application
- Check browser console for errors
- Verify API is enabled in Google Cloud Console

---

## Alternative: Use Without Google Maps

If you don't want to use Google Maps API, the system will still work:

1. **Browser GPS + WiFi**: Uses device's built-in positioning
2. **Manual Entry**: Teachers can enter coordinates manually
3. **Saved Locations**: Reuse previous lecture locations

**Accuracy without Google API:**
- Outdoors: ±10-30m (good)
- Indoors: ±50-200m (poor)

**Accuracy with Google API:**
- Outdoors: ±5-15m (excellent)
- Indoors: ±10-50m (good)

---

## Security Best Practices:

### 1. Restrict API Key:
- ✅ Only allow Geolocation API
- ✅ Only allow your domain
- ✅ Set spending limits

### 2. Monitor Usage:
- Check Google Cloud Console monthly
- Set up billing alerts
- Review API usage logs

### 3. Keep Key Secret:
- ✅ Never commit `.env` file to git
- ✅ Use environment variables in production
- ✅ Rotate key if exposed

---

## Troubleshooting:

### "API key not valid" Error:
- Check key is copied correctly (no spaces)
- Verify Geolocation API is enabled
- Check domain restrictions

### "Quota exceeded" Error:
- You've used 40,000 requests this month
- Wait until next month or upgrade
- Check for API key leaks

### Still Getting Poor Accuracy:
- Google API might not have WiFi data for your area
- Try moving near windows
- Use manual entry as fallback

---

## Support:

- Google Maps Platform Support: https://developers.google.com/maps/support
- API Documentation: https://developers.google.com/maps/documentation/geolocation
- Pricing Calculator: https://mapsplatform.google.com/pricing/

---

## Summary:

1. ✅ Create Google Cloud project
2. ✅ Enable Geolocation API
3. ✅ Create and restrict API key
4. ✅ Add to `.env` file
5. ✅ Restart application
6. ✅ Test location accuracy

**Total Time**: 5 minutes
**Cost**: FREE (for typical usage)
**Benefit**: Much better indoor accuracy! 🎯
