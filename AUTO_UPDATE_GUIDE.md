# Auto-Update Guide

## How Auto-Updates Work

The app automatically checks for updates on startup and downloads them in the background. When an update is ready, a notification appears at the top of the window with a button to install it.

## How to Trigger an Update

### 1. **Bump Version in `package.json`**
```json
{
  "version": "1.0.4"  // Increment this
}
```

### 2. **Commit and Tag**
```bash
git add package.json
git commit -m "Bump version to 1.0.4"
git tag v1.0.4
git push origin main
git push origin v1.0.4
```

### 3. **GitHub Actions Builds & Publishes**
- The workflow `.github/workflows/build-windows.yml` triggers automatically
- Creates a GitHub release with tag `v1.0.4`
- Uploads the `.exe` installer to the release

### 4. **Users Get Auto-Updated**
- Next time they open the app, it checks for updates
- Downloads the new version in background
- Shows "Update available" notification
- Click "Restart and Update" to install

## Testing Updates

1. Build v1.0.3: `npm run build:win`
2. Install the app from `dist/*.exe`
3. Bump version to v1.0.4, commit, and push tag
4. Wait for GitHub Actions to build
5. Open the installed app → it will detect and download v1.0.4
6. Click the update button to install

## Notes

- Updates only work in **production builds**, not dev mode
- First time users must manually download and install the app
- Subsequent updates are automatic
- No code signing configured (users may see security warnings on Windows)
