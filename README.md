# ify
ify is a web application built with **Vite** on the frontend and **Flask** on the backend. 
It connects to the Last.fm API, aggregates your top community music tags and scores your taste profile (temporarily) against custom emoji configurations.

## Privacy
Your data is processed entirely in-memory and retrieved live from Last.fm on-demand. There is no database attached to this application.
The app handles logins through Last.fm's secure native application gateway. Active user credentials stay private within your browser's encrypted session tokens.

