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
