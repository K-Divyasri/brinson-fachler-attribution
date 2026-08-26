# Hosting the Brinson-Fachler dashboard

The app is a single Streamlit file (`build_from_scratch/app.py`) with no database,
no API keys, and no external service calls -- every number on screen comes from
synthetic data generated in-process (`attribution/data.py`). That makes hosting
close to the easiest case there is: no secrets to configure, no persistent storage,
no rate limits to worry about. Three ways to put it online, cheapest/simplest
first:

1. **Streamlit Community Cloud** -- free, no card, no Docker knowledge needed.
   Recommended if you just want a shareable URL fast.
2. **Hugging Face Spaces** -- free, also no Docker knowledge needed, useful if
   you already have an HF account or want the project visible on that platform
   too.
3. **Docker on Render / Railway / Fly** -- more control, same container everywhere,
   uses the Dockerfile in this folder (already verified locally, see below) --
   worth doing if you want the exact same artifact running in every environment,
   or you're practicing the Docker-hosting skill itself.

You do not need to pick just one. Options 1 and 3 (or 2 and 3) can run side by
side pointing at the same GitHub repo.

---

## Before any of this: get the code on GitHub

All three options deploy from a GitHub repo, not from your laptop directly. If
you haven't already:

```powershell
cd C:\Users\divya\Downloads\learning\41-brinson-fachler-attribution
git init
git add .
git commit -m "Initial commit: Brinson-Fachler attribution project"
git branch -M main
```

Then create a new **empty** repository on github.com (no auto-README, no
license, no .gitignore -- those already exist locally and an auto-generated one
will conflict), and:

```powershell
git remote add origin https://github.com/YOURNAME/brinson-fachler-attribution.git
git push -u origin main
```

This makes `41-brinson-fachler-attribution/` the repo root, with the real code
one level down in `build_from_scratch/` -- the same shape used across this whole
learning repo. Every path below assumes that shape.

**If you instead push the entire `learning` folder as one big monorepo** (every
numbered project in one repo), the same steps work, but every path you type into
a hosting provider's UI needs the extra prefix:
`41-brinson-fachler-attribution/build_from_scratch/app.py` instead of just
`build_from_scratch/app.py`. Streamlit Community Cloud in particular looks for
`requirements.txt` in the same directory as the app file first; if it ever fails
to resolve dependencies in a monorepo layout, the fallback is copying
`requirements.txt` to the true repo root as well (harmless duplication, not a
problem to have both).

---

## Option 1 -- Streamlit Community Cloud (recommended, easiest)

Free, hosted by the makers of Streamlit itself, no credit card.

1. Go to https://share.streamlit.io and sign in with your GitHub account.
2. Click **Create app** -> **Deploy a public app from GitHub**.
3. Fill in the three fields:
   - **Repository**: `YOURNAME/brinson-fachler-attribution` (or whatever you
     named it)
   - **Branch**: `main`
   - **Main file path**: `build_from_scratch/app.py` (or, if you pushed the
     whole `learning` monorepo instead:
     `41-brinson-fachler-attribution/build_from_scratch/app.py`)
4. Click **Deploy**. First build takes a minute or two -- it reads
   `build_from_scratch/requirements.txt` (`streamlit>=1.32`, `plotly>=5.20`,
   `pytest>=8.0`), installs them, and starts the app.
5. You get a URL like `https://yourname-brinson-fachler-attribution.streamlit.app`.
   Put it in your GitHub repo description and the root `README.md`.

No secrets to add in **Advanced settings** -- leave that section empty. If the
build fails with "requirements.txt not found," it's almost always the monorepo
path issue above; copy `requirements.txt` to the actual repo root as a fallback.

Free-tier honesty: Community Cloud apps sleep after a period of no traffic and
take a few seconds to wake on the next visit. Normal, not a bug.

---

## Option 2 -- Hugging Face Spaces

Also free, also no Docker knowledge required.

1. Sign up / sign in at https://huggingface.co.
2. Click your profile -> **New Space**.
3. Give it a name, pick **Streamlit** as the Space SDK, choose **Public** visibility.
4. HF creates a small git repo for the Space. Either:
   - Push this project's `build_from_scratch/` contents (app.py, requirements.txt,
     attribution/, .streamlit/) straight into the Space repo's root, or
   - Clone the Space repo locally and copy the files in, then `git add . && git
     commit -m "Add app" && git push`.
5. HF Spaces looks for `app.py` and `requirements.txt` at the Space repo's root by
   default -- that's why the contents of `build_from_scratch/` (not the whole
   project folder) go directly into the Space repo, unlike Streamlit Cloud which
   can point at a subfolder of a larger repo.
6. The Space builds automatically on push. Visit
   `https://huggingface.co/spaces/YOURNAME/YOURSPACE` once it says **Running**.

No secrets/variables needed in the Space's **Settings** tab.

---

## Option 3 -- Docker on Render, Railway, or Fly (already verified)

Use this path if you want the identical container running the same way in every
environment, or you're specifically practicing the Docker-hosting skill.

**The Dockerfile in this folder has already been verified on this machine** (see
the header comment inside `hosting/Dockerfile` and CANON section 3 of this
project's build notes):

```
docker build -t brinson-fachler .
docker run -p 8501:8501 brinson-fachler
curl http://localhost:8501/_stcore/health
```

- `docker build` succeeded.
- `docker run` started the container cleanly.
- `curl http://localhost:8501/_stcore/health` returned **HTTP 200**.
- Container logs were clean (no tracebacks, no warnings).
- Cleanup (`docker stop` / `docker rm`) succeeded with no leftover state.

That was already run and confirmed -- there's no need to redo it yourself before
trusting this Dockerfile; it's cited here as a verified fact, not a claim to
re-check. Feel free to re-run it anyway if you want to see it locally first, or
after you change `requirements.txt` or `app.py`.

Because the Dockerfile already lives permanently inside `build_from_scratch/`
(unlike some other projects on this track, nothing needs to be copied in first),
deploying is just pointing a host at that subfolder:

### Render (matches the rest of this learning repo's convention)

1. Sign up free at https://render.com (sign in with GitHub, no card needed).
2. **New** -> **Web Service**, connect your repo.
3. Set **Root Directory** to `build_from_scratch` (or
   `41-brinson-fachler-attribution/build_from_scratch` if you pushed the whole
   monorepo). Runtime: **Docker**. Render finds the `Dockerfile` there.
4. Leave the health-check path as `/_stcore/health` (or set it explicitly) --
   this is the one Streamlit route that actually returns 200, matching what was
   already verified locally.
5. Deploy. Render injects its own `PORT` environment variable at start; the
   Dockerfile's `CMD` already reads `${PORT}` (falling back to 8501 only when
   it's unset) -- no action needed on your side.
6. You get a URL like `https://brinson-fachler.onrender.com`.

Free-tier honesty: Render's free web services spin down after roughly 15 minutes
of no traffic and take 30-60 seconds to wake back up on the next request.

### Railway

1. Sign up free at https://railway.app (GitHub sign-in).
2. **New Project** -> **Deploy from GitHub repo**.
3. In the service settings, set the **Root Directory** to `build_from_scratch`
   (same monorepo caveat as above). Railway auto-detects the Dockerfile.
4. Railway also injects `PORT` automatically -- the Dockerfile already handles it.
5. Deploy, then open the generated `*.up.railway.app` URL.

### Fly.io

1. Install the Fly CLI (https://fly.io/docs/flyctl/install/) and run `fly auth
   signup` (or `fly auth login` if you already have an account).
2. From `build_from_scratch/`:

   ```powershell
   cd build_from_scratch
   fly launch
   ```

   Answer the prompts (app name, region); when asked whether to deploy now, say
   yes. `fly launch` detects the existing `Dockerfile` and uses it as-is.
3. Fly sets its own `PORT` (usually 8080) via the `internal_port` in the
   generated `fly.toml`, or you can leave the Dockerfile's own `${PORT}` handling
   in place and set `internal_port = 8501` in `fly.toml` to match what the
   container actually listens on when `PORT` is unset.
4. `fly deploy` for subsequent updates.

---

## What you do NOT need for any of these options

- No API keys.
- No database or persistent volume -- every dataset is regenerated in-process
  from a fixed seed (`seed=7`) each time the app starts.
- No secrets manager, no `.env` file, no `st.secrets` entries.

The only thing that ever needs to exist alongside the app is
`requirements.txt` and (optionally, for the Streamlit theme) `.streamlit/config.toml`
-- both already present in `build_from_scratch/`.

## Troubleshooting

- **"ModuleNotFoundError: No module named 'attribution'"** -- the app was started
  from the wrong working directory, or the host's root directory setting points
  one level too high or low. `app.py` imports `attribution.*` as a sibling
  package, so the process's working directory must be `build_from_scratch/`
  itself.
- **Streamlit Cloud can't find requirements.txt** -- almost always the monorepo
  path issue described above. Copy `requirements.txt` to the actual repo root as
  a fallback.
- **Health check fails on a Docker host** -- confirm the health-check path is
  exactly `/_stcore/health`, not `/` or `/health`. Streamlit's own health route is
  the only one that returns 200 by default.
- **Container builds but the page never loads** -- check that `--server.address
  =0.0.0.0` is present in the Dockerfile's `CMD` (it is). Binding to
  `127.0.0.1` instead would make the app unreachable from outside the container,
  the same class of bug as every other Dockerized Streamlit app on this track.
