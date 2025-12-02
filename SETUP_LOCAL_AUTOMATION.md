# Local Automation Setup for Windows

This guide will help you set up automatic daily scraping of KenPom data on your Windows machine.

## Prerequisites

1. **Python installed** - You should already have this since the scrapers work
2. **Git installed** - Download from https://git-scm.com/download/win if needed
   - Alternatively, install via Windows Package Manager: `winget install Git.Git`
3. **Your computer must be on** at the scheduled time for the scraper to run
4. **KenPom credentials** - Make sure your `.env` file has your login credentials
   - Create a `.env` file in the project root directory with the following format:
   ```
   KENPOM_USERNAME=your_username
   KENPOM_PASSWORD=your_password
   ```
   - Replace `your_username` and `your_password` with your actual KenPom credentials

## Step 1: Verify Prerequisites

1. Open Command Prompt (press `Win + R`, type `cmd`, press Enter)
2. Test Python: `python --version`
3. Test Git: `git --version`

If either command fails, install the missing software.

## Step 2: One-Time Setup

1. **Configure Git Credentials** (so pushing doesn't require password every time):
   
   Open Command Prompt in your project folder and run:
   ```
   git config credential.helper manager-core
   ```
   
   This uses Windows Credential Manager for secure credential storage. The next time you push, Git will ask for your credentials and Windows will securely store them.
   
   **Alternative (less secure):** If the above doesn't work, you can use:
   ```
   git config credential.helper store
   ```
   Note: This stores credentials in plain text, so use Windows Credential Manager when possible.

2. **Test the Scripts Manually**:
   
   Double-click `run_and_push.bat` to test if everything works. 
   
   You should see:
   - The scrapers run successfully
   - Data gets committed and pushed to GitHub
   
   If you see errors, fix them before proceeding to automation.

## Step 3: Set Up Windows Task Scheduler

### Option A: Using the GUI (Easiest)

1. **Open Task Scheduler**:
   - Press `Win + R`
   - Type `taskschd.msc`
   - Press Enter

2. **Create a New Task**:
   - Click "Create Basic Task..." in the right panel
   - Name: `KenPom Daily Scraper`
   - Description: `Automatically scrapes KenPom data and pushes to GitHub`
   - Click Next

3. **Set the Trigger** (when it runs):
   - Select "Daily"
   - Click Next
   - Set your preferred time (e.g., 2:00 AM when your computer is on but you're not using it)
   - Click Next

4. **Set the Action**:
   - Select "Start a program"
   - Click Next
   - Program/script: Browse to your `run_and_push.bat` file
   - Start in: Enter the folder path where your project is (e.g., `C:\Users\YourName\kp_test`)
   - Click Next

5. **Finish**:
   - Check "Open the Properties dialog..."
   - Click Finish

6. **Configure Additional Settings**:
   In the Properties dialog that opens:
   - Go to the "Conditions" tab
   - Uncheck "Start the task only if the computer is on AC power" (if laptop)
   - Go to the "Settings" tab
   - Check "Run task as soon as possible after a scheduled start is missed"
   - Click OK

### Option B: Using PowerShell (Advanced)

Run this PowerShell command (replace the path with your actual project path):

```powershell
$action = New-ScheduledTaskAction -Execute "C:\Users\YourName\kp_test\run_and_push.bat" -WorkingDirectory "C:\Users\YourName\kp_test"
$trigger = New-ScheduledTaskTrigger -Daily -At "2:00AM"
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName "KenPom Daily Scraper" -Action $action -Trigger $trigger -Settings $settings -Description "Automatically scrapes KenPom data"
```

## Step 4: Test the Scheduled Task

1. In Task Scheduler, find your task in the list
2. Right-click it and select "Run"
3. Watch the Command Prompt window that opens
4. Verify the data appears on GitHub

## Troubleshooting

### The task runs but doesn't push to GitHub
- Make sure you ran `git config credential.helper manager-core` (or `store`)
- Manually run `git push` once in Command Prompt to save credentials

### Python or Git not found
- The Task Scheduler might not have the same PATH as your user account
- Edit the task and set the full path to Python in the batch file:
  ```
  "C:\Python310\python.exe" scrape_kenpom_stats.py
  ```

### Task doesn't run when computer is asleep
- Your computer needs to be on (not sleeping) for the task to run
- Either leave it on, or adjust your power settings
- Or change the schedule to a time when you normally use your computer

### Still getting Cloudflare blocks locally
- This shouldn't happen on your home network
- If it does, try:
  - Running the script at different times
  - Checking if your ISP IP is flagged
  - Using a VPN

## Viewing Logs

The Task Scheduler keeps logs of every run:
1. Open Task Scheduler
2. Click on "Task Scheduler Library" in the left panel
3. Find your task
4. Click the "History" tab at the bottom

## Changing the Schedule

1. Open Task Scheduler
2. Find your task
3. Right-click → Properties
4. Go to "Triggers" tab
5. Edit the trigger to change time/frequency

## Disabling the Automation

1. Open Task Scheduler
2. Find your task
3. Right-click → Disable (or Delete to remove completely)

## Support

If you run into issues:
1. Check the Task Scheduler History
2. Try running `run_and_push.bat` manually to see the error
3. Make sure your `.env` file has the correct credentials
4. Verify your computer was on at the scheduled time
