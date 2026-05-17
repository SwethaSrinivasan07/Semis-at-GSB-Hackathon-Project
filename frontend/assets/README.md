# Frontend Assets

Drop static images used by the Streamlit app here.

## Expected files

- `datacenter.jpg` — Hero image for the view-magnifier section on the
  landing page (data-center fiber patch panel, ideally landscape, ~1400px
  wide). If absent, the app falls back to a stock Unsplash photo.

The Python code in `manufacturer_app.py` base64-encodes these files at
render time and embeds them in the iframe, so no static-serving config
is required on the Streamlit side.
