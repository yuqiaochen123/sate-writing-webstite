# Netlify Deployment Guide

## Quick Netlify Setup

### Step 1: Deploy Frontend to Netlify

1. **Go to [netlify.com](https://netlify.com)** and sign up/login
2. **Click "New site from Git"**
3. **Connect your GitHub account** and select your repository
4. **Configure build settings**:
   - **Build command**: Leave empty (your site is already built)
   - **Publish directory**: `.` (root directory)
   - **Branch**: `main` (or your default branch)
5. **Click "Deploy site"**
6. **Get your Netlify URL** (e.g., `https://your-app-name.netlify.app`)

### Step 2: Deploy Backend to Railway

1. **Go to [railway.app](https://railway.app)** and sign up
2. **Create new project** → **Deploy from GitHub repo**
3. **Select your repository**
4. **Configure the service**:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
5. **Deploy and get your Railway URL** (e.g., `https://your-backend.railway.app`)

### Step 3: Connect Frontend and Backend

1. **Update your `config.js`**:
   ```javascript
   const CONFIG = {
       environment: 'deployed',
       
       local: {
           baseUrl: 'http://127.0.0.1:5001'
       },
       
       deployed: {
           baseUrl: 'https://your-backend.railway.app'  // Your Railway URL
       }
   };
   ```

2. **Commit and push your changes** to GitHub
3. **Netlify will automatically redeploy** with the updated configuration

### Step 4: Test Your Deployment

1. **Visit your Netlify URL** (e.g., `https://your-app-name.netlify.app`)
2. **Try analyzing a bass line** - it should call your Railway backend
3. **Check the browser console** for any errors

## Custom Domain (Optional)

1. **In Netlify dashboard**, go to **Site settings** → **Domain management**
2. **Add custom domain** (if you have one)
3. **Configure DNS** as instructed by Netlify

## Environment Variables (Optional)

You can set environment variables in Netlify:

1. **Go to Site settings** → **Environment variables**
2. **Add variables** like:
   - `BACKEND_URL`: `https://your-backend.railway.app`

## Troubleshooting

### Common Issues:

1. **CORS errors**: Make sure your Railway backend has CORS enabled
2. **404 errors**: Check that your `netlify.toml` file is in the root directory
3. **Build failures**: Your site doesn't need a build step, so leave build command empty

### Debugging:

- **Check Netlify deploy logs** in the dashboard
- **Check Railway logs** in the Railway dashboard
- **Test your backend directly**: `curl https://your-backend.railway.app/health`
- **Check browser console** for JavaScript errors

## Example URLs

After deployment, you'll have:
- **Frontend**: `https://satb-writer.netlify.app`
- **Backend**: `https://satb-backend.railway.app`

Users can access your app at the Netlify URL, and it will automatically call your Railway backend for analysis and SATB generation.

## Benefits of This Setup

✅ **Free hosting** for both frontend and backend  
✅ **Automatic deployments** when you push to GitHub  
✅ **Global CDN** for fast loading  
✅ **SSL certificates** included  
✅ **Custom domains** supported  
✅ **No server maintenance** required  

Your app will be accessible to anyone with the URL, and you won't need to run anything locally!
