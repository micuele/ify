# ify
ify is a web application built with **Vite** on the frontend and **Flask** on the backend. 
It maps Last.fm listening data and Letterboxd/TMDB film data into the same
24-category visual vibe system. Both providers select one of the same numbered
output images.

The category catalog is available at `GET /api/vibes`. Image files belong in
`frontend/public/output-images/` as `01.png` through `24.png`.

## Privacy
Your data is processed entirely in-memory and retrieved live from Last.fm,
Letterboxd, and TMDB on demand. There is no database attached to this
application. The app handles logins through Last.fm's secure native application
gateway. Active user credentials stay private within your browser's encrypted
session tokens.
