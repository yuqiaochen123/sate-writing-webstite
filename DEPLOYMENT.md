# Deployment Guide for SATB Writing Website

This guide will help you deploy your Flask backend so it can be accessed by other users without running locally.

## Option 1: Deploy to Railway (Recommended - Free Tier)

Railway is a modern platform that's easy to use and has a generous free tier.

### Steps:
1. **Sign up** at [railway.app](https://railway.app)
2. **Install Railway CLI** (optional but helpful):
   ```bash
   npm install -g @railway/cli
   ```
3. **Deploy your backend**:
   ```bash
   cd backend
   railway login
   railway init
   railway up
   ```
4. **Get your deployment URL** from the Railway dashboard
5. **Update config.js**:
   ```javascript
   deployed: {
       baseUrl: 'https://your-railway-app-name.railway.app'
   }
   ```
6. **Switch to deployed environment**:
   ```javascript
   environment: 'deployed'
   ```

## Option 2: Deploy to Render (Free Tier)

Render is another excellent option with a free tier.

### Steps:
1. **Sign up** at [render.com](https://render.com)
2. **Create a new Web Service**
3. **Connect your GitHub repository** (you'll need to push your code to GitHub first)
4. **Configure the service**:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Environment**: Python 3
5. **Deploy** and get your URL
6. **Update config.js** with your Render URL

## Option 3: Deploy to Heroku (Paid)

Heroku no longer has a free tier, but it's still popular.

### Steps:
1. **Sign up** at [heroku.com](https://heroku.com)
2. **Install Heroku CLI**:
   ```bash
   # macOS
   brew tap heroku/brew && brew install heroku
   ```
3. **Deploy**:
   ```bash
   cd backend
   heroku create your-app-name
   git add .
   git commit -m "Deploy to Heroku"
   git push heroku main
   ```
4. **Update config.js** with your Heroku URL

## Option 4: Deploy to Vercel (Free Tier)

Vercel is great for Python apps and has a free tier.

### Steps:
1. **Sign up** at [vercel.com](https://vercel.com)
2. **Install Vercel CLI**:
   ```bash
   npm install -g vercel
   ```
3. **Create vercel.json** in your backend folder:
   ```json
   {
     "version": 2,
     "builds": [
       {
         "src": "app.py",
         "use": "@vercel/python"
       }
     ],
     "routes": [
       {
         "src": "/(.*)",
         "dest": "app.py"
       }
     ]
   }
   ```
4. **Deploy**:
   ```bash
   cd backend
   vercel
   ```

## Option 5: Netlify Frontend + Backend Deployment

This is a great combination: deploy your frontend to Netlify and your backend to Railway/Render.

### Frontend on Netlify:
1. **Sign up** at [netlify.com](https://netlify.com)
2. **Connect your GitHub repository**
3. **Configure build settings**:
   - **Build command**: Leave empty (no build needed)
   - **Publish directory**: `.` (root directory)
4. **Deploy** and get your frontend URL

### Backend on Railway/Render:
Follow the steps above for Railway or Render to deploy your Flask backend.

### Connect them:
1. **Update config.js** with your backend URL:
   ```javascript
   deployed: {
       baseUrl: 'https://your-backend-url.railway.app'
   }
   ```
2. **Switch to deployed environment**:
   ```javascript
   environment: 'deployed'
   ```

## Option 6: Deploy Frontend and Backend Together

For a complete solution, you can also deploy your frontend:

### Frontend Deployment Options:
1. **GitHub Pages** (Free)
2. **Netlify** (Free)
3. **Vercel** (Free)
4. **Firebase Hosting** (Free)

### Steps for GitHub Pages:
1. **Push your code to GitHub**
2. **Go to Settings > Pages**
3. **Select source branch** (usually `main`)
4. **Your site will be available at**: `https://yourusername.github.io/your-repo-name`

## Testing Your Deployment

After deployment:

1. **Update config.js** with your deployed backend URL
2. **Change environment to 'deployed'**:
   ```javascript
   environment: 'deployed'
   ```
3. **Test the application** by opening your frontend URL
4. **Verify that API calls work** by trying to analyze a bass line

## Environment Variables (Optional)

For better security, you can use environment variables:

```bash
# In your deployment platform, set:
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
```

## Troubleshooting

### Common Issues:
1. **CORS errors**: Make sure your backend has CORS properly configured
2. **Port issues**: The deployment platforms will set their own PORT environment variable
3. **Dependencies**: Make sure all dependencies are in `requirements.txt`
4. **File paths**: Use relative paths in your code

### Debugging:
- Check deployment logs in your platform's dashboard
- Test your API endpoints directly using curl or Postman
- Verify your frontend can reach your backend URL

## Quick Start (Recommended: Netlify + Railway)

1. **Push your code to GitHub**
2. **Deploy backend to Railway**:
   - Go to [railway.app](https://railway.app)
   - Create new project from GitHub
   - Set build command: `pip install -r requirements.txt`
   - Set start command: `gunicorn app:app`
3. **Deploy frontend to Netlify**:
   - Go to [netlify.com](https://netlify.com)
   - Connect your GitHub repository
   - Deploy with default settings
4. **Update config.js** with your Railway backend URL
5. **Switch to deployed environment**

Your app will now be accessible to anyone with the Netlify URL!

## Complete Deployment Example

Here's a complete example of the recommended setup:

1. **Backend URL**: `https://satb-backend.railway.app`
2. **Frontend URL**: `https://satb-writer.netlify.app`
3. **config.js**:
   ```javascript
   deployed: {
       baseUrl: 'https://satb-backend.railway.app'
   }
   environment: 'deployed'
   ```

Users can then access your app at `https://satb-writer.netlify.app` and it will call your deployed backend automatically.
