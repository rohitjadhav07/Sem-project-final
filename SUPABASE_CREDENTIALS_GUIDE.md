# 🔑 Supabase Credentials - Quick Reference

## 📍 Where to Find Each Credential

### 1. SUPABASE_URL & API Keys
```
🏠 Supabase Dashboard
└── ⚙️ Settings (left sidebar)
    └── 🔌 API
        ├── 📋 Configuration
        │   └── 🌐 Project URL ← SUPABASE_URL
        └── 🔑 Project API keys
            ├── 👥 anon public ← SUPABASE_ANON_KEY
            └── 🔒 service_role secret ← SUPABASE_SERVICE_ROLE_KEY ⭐
```

### 2. SUPABASE_DATABASE_URL
```
🏠 Supabase Dashboard
└── ⚙️ Settings (left sidebar)
    └── 🗄️ Database
        └── 📡 Connection info
            └── 🔗 Connection string
                └── 📝 URI ← SUPABASE_DATABASE_URL
```

## 🎯 Step-by-Step Screenshots Guide

### Getting API Keys (Settings → API):

1. **Click Settings** in left sidebar
2. **Click API** under Settings
3. **Scroll to "Project API keys"**
4. **Copy both keys:**
   - `anon` `public` = **SUPABASE_ANON_KEY**
   - `service_role` `secret` = **SUPABASE_SERVICE_ROLE_KEY**

### Getting Database URL (Settings → Database):

1. **Click Settings** in left sidebar
2. **Click Database** under Settings
3. **Scroll to "Connection info"**
4. **Click "Connection string"**
5. **Click "URI" tab**
6. **Copy the PostgreSQL URL**
7. **Replace `YOUR_PASSWORD` with your actual database password**

## ⚠️ Important Notes

- **Service Role Key**: Has admin privileges, keep it secret!
- **Database Password**: Use the password you set when creating the project
- **Connection String**: The format might vary slightly, but always starts with `postgresql://`

## 🧪 Test Your Setup

After setting up, visit: `/test/supabase` to verify all credentials are working!

## 🆘 Common Issues

### "Invalid API Key"
- Double-check you copied the full key (they're very long!)
- Make sure no extra spaces at beginning/end

### "Connection Failed"
- Verify database password is correct
- Check if your Supabase project is active (not paused)

### "Not Found"
- Ensure Project URL is correct
- Check if project region matches the URL

## 📞 Need Help?

If you're still having trouble:
1. Check the Supabase dashboard for any error messages
2. Verify your project is fully created and active
3. Try regenerating the API keys if needed