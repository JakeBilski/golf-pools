# Golf Betting Pool — Setup Guide

## Hosting: GitHub Pages (free)

### First-time setup

1. Create a free account at **github.com**
2. Click **New repository** — name it anything (e.g. `golf-pool`)
3. Set it to **Public**
4. Upload all these files to the repo:
   - `index.html`
   - `scores.json`
   - `tournament-id.txt`
   - `.github/workflows/fetch-scores.yml`
5. Go to **Settings -> Pages -> Source -> Deploy from branch -> main**
6. Your site will be live at `https://YOUR-USERNAME.github.io/golf-pool`

---

## Live Scoring (each tournament)

1. Go to espn.com/golf/leaderboard and navigate to your tournament
2. Copy the ID from the URL: `.../tournamentId/401811938`
3. Edit `tournament-id.txt` in your repo — replace with the new ID and commit
4. The workflow runs automatically every 5 min Thu-Sun
5. To trigger immediately: repo -> Actions -> Fetch Golf Scores -> Run workflow
6. In your site: Admin -> Live Scoring Config -> Test & Preview to confirm

---

## How it works

Every 5 minutes during tournament hours, GitHub Actions fetches ESPN
and saves the result to scores.json in your repo. Your site reads that
file directly — no server, no API keys, completely free.

## Admin password
Default: caddie2025
