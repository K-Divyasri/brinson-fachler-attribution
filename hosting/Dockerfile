# Exact copy of the repo-root Dockerfile, kept here for reference and for
# hosting providers that expect a Dockerfile at a predictable, documented path.
# Unlike some other projects on this track, nothing needs to be copied INTO
# the repo root before building -- the root Dockerfile already lives there
# permanently as part of the shipped, pytest-verified package (see
# README.md's project-structure listing). If the two files
# ever drift, the repo-root Dockerfile is the one that's authoritative;
# update this copy to match.
#
# Already verified on this machine (see CANON section 3 / HOSTING_GUIDE.md):
#   docker build -t brinson-fachler .   -> succeeded
#   docker run -p 8501:8501 brinson-fachler   -> started clean, logs clean
#   curl http://localhost:8501/_stcore/health -> HTTP 200
#   container stopped and removed with no leftover state
# Do not re-run this to "confirm" it works -- it already does. Re-run it only
# if you change requirements.txt, app.py, or this file itself.
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# $PORT is provided by most hosts (Render/Railway/Fly). Fallback to 8501 locally.
CMD streamlit run app.py --server.port=${PORT:-8501} --server.address=0.0.0.0 --server.headless=true
