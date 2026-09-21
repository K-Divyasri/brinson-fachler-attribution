# Deploy checklist -- Brinson-Fachler attribution dashboard

This project's "definition of done" for shipping the dashboard somewhere public.
Walk it top to bottom. Do not tick a box you have not actually verified by running
the command -- "should work" is not the same as "works." Commands assume you are
at the repo root unless noted.

## Runs locally, offline

- [ ] Fresh virtual environment, dependencies installed cleanly:
      `python -m venv .venv ; .\.venv\Scripts\Activate.ps1` then
      `pip install -r requirements.txt`.
- [ ] `python smoke_test.py` prints the single-period, linked, and risk-attribution
      figures and ends with `OK: all reconciliation identities hold.`
- [ ] `pytest -q` is all green: **20 passed**.
- [ ] `streamlit run app.py` opens at `http://localhost:8501` with all three tabs
      (single-period, linked, risk) rendering without a traceback.

## Config files present

- [ ] `requirements.txt` exists and pins real, installable
      versions (`streamlit>=1.32`, `plotly>=5.20`, `pytest>=8.0`).
- [ ] `.streamlit/config.toml` exists (headless server mode,
      usage-stats gathering off, theme set).
- [ ] If deploying from a monorepo (the whole `learning` folder as one repo, not
      just this project), a copy of `requirements.txt` exists at the true repo
      root as a fallback for dependency resolution -- see `HOSTING_GUIDE.md`'s
      monorepo note.

## No secrets needed -- and none present

- [ ] No API key, token, or credential is referenced anywhere in
      `attribution/` or `app.py`. There shouldn't be one to find: every dataset
      is synthetic, generated in-process from a fixed seed.
- [ ] No `.env` file exists at the repo root, and none is required.
- [ ] No entries needed in any host's "secrets" / "environment variables" panel
      (Streamlit Cloud's Advanced Settings, HF Spaces' Settings tab, Render's
      Environment tab, etc.) -- leave them empty.
- [ ] `git status` / `git ls-files` show nothing that looks like a credential
      (`*.pem`, `*.key`, `credentials.json`, a bare `.env`).

## Health check endpoint

- [ ] The app exposes Streamlit's built-in health route at `/_stcore/health`
      (no custom code needed -- it ships with Streamlit itself).
- [ ] **Already verified on this machine**: `curl http://localhost:8501/_stcore/health`
      returned **HTTP 200** against the container built from
      the repo-root `Dockerfile` (see CANON section 3 / `HOSTING_GUIDE.md`).
      Not something you need to re-run to trust -- only re-verify if you change
      `app.py` or the Dockerfile.
- [ ] Any Docker host's health-check path setting points at `/_stcore/health`
      specifically, not `/`.

## Docker (if using the container path)

- [ ] `docker build -t brinson-fachler .` succeeds from the
      repo root (Dockerfile already lives there permanently -- no
      copy-in step needed, unlike some other projects on this track).
- [ ] `docker run -p 8501:8501 brinson-fachler` starts cleanly with no
      traceback in the logs.
- [ ] `curl http://localhost:8501/_stcore/health` returns 200 (already confirmed
      once -- see above).
- [ ] Container stopped and removed cleanly (`docker stop` / `docker rm`), no
      leftover volumes or dangling state.

## Pushed to GitHub

- [ ] Repo created (empty, no auto-README/license) and pushed, with
      `41-brinson-fachler-attribution/` as the repo root (or the whole
      `learning` monorepo, noting the extra path prefix everywhere if so).
- [ ] `git status` shows a clean working tree; `git ls-files` reviewed for
      anything that shouldn't be public.
- [ ] Files visible on the GitHub repo page after a refresh.

## CI is green

- [ ] `.github/workflows/tests.yml` (copied from
      `hosting/github_actions/tests.yml`) is committed and pushed.
- [ ] The Actions tab shows a completed green run: install
      `requirements.txt`, then `pytest -q` from the repo root,
      reporting **20 passed**.
- [ ] No secret is configured on the repo for this workflow, and none is needed
      -- every test is pure offline math on synthetic data.

## Deployed and reachable

- [ ] Picked at least one of: Streamlit Community Cloud, Hugging Face Spaces,
      Docker on Render/Railway/Fly (see `HOSTING_GUIDE.md`).
- [ ] Visited the live URL and confirmed all three tabs load with real numbers,
      not a build-failure page.
- [ ] Live URL added to the project's root `README.md` and the GitHub repo
      description.

## Repo pinned

- [ ] Pinned on your GitHub profile (**Customize your pins**) so it's one of
      the first things a recruiter sees.

When every box is ticked, the project is presentable. There is nothing in this
project that needs a secret, a database, or a paid tier at any point in this
list -- if you find yourself about to add one, stop and check `HOSTING_GUIDE.md`
first.
