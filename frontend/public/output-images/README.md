# Output images

Add the 24 final images to this directory using two-digit filenames:

```text
01.png
02.png
...
24.png
```

PNG, WebP, JPG, and JPEG are supported. The frontend displays a numbered
placeholder when an image is missing. Flask serves this directory directly at
`/output-images/`, and Vite also copies it into production builds.

The filename-to-vibe mapping is defined by `GET /api/vibes` and
`backend/app/vibes.py`. Both Last.fm and Letterboxd return the same
`selected_output.image_key` values.

| Image | Category |
| --- | --- |
| `01` | Pop & Comedy |
| `02` | Romance & Soul |
| `03` | Drama & Melancholy |
| `04` | Indie & Introspection |
| `05` | Fantasy & Dream Pop |
| `06` | Ambient & Slow |
| `07` | Folk, Country & Western |
| `08` | Classics, History & Nostalgia |
| `09` | Animation, Family & Indie Pop |
| `10` | Jazz, Blues & Style |
| `11` | Dance, Electronic & Music |
| `12` | Latin & Global Rhythm |
| `13` | Hip-Hop & Urban Stories |
| `14` | Rock, Punk & Rebellion |
| `15` | Metal, Action & Adrenaline |
| `16` | Horror, Gothic & Dark Music |
| `17` | Thriller, Industrial & Tension |
| `18` | Crime, Mystery & Noir |
| `19` | Psychedelia & Surrealism |
| `20` | Experimental & Art House |
| `21` | Sci-Fi, Electronic & Future |
| `22` | Adventure, War & Epic |
| `23` | Documentary, Classical & Ideas |
| `24` | Hyperpop, Satire & Chaos |
