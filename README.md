# Kosme Backend 💙

## FastAPI & Supabase 🥶

### Useful Scripts 🤣

1. `update-dependencies.sh`

### Set Up 🤩

1. Clone this repo

2. Install the **Ruff VSCode extension** (static analysis tool)
3. Configure project-level/user-level VSCode settings

   ```
    # settings.json
    "[python]": {
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
        "source.fixAll": "explicit",
        "source.organizeImports": "explicit"
        },
        "editor.defaultFormatter": "charliermarsh.ruff"
    }
   ```

   <br>

4. Go into the root directory
   ```
   cd kosme-backend
   ```
5. Create the virtual environment
   ```
   python -m venv venv
   ```
6. Activate the virtual environment

   ```
   # Windows
   venv\Scripts\activate

   # MacOS
   source venv/bin/activate
   ```

7. Install the requirements

   ```
   cd .scripts
   bash update-dependencies.sh

   cd ..
   pip install -r .requirements/requirements.txt
   ```

   <br>

8. Create the `.env` file
   ```
   touch .env
   ```
9. Populate the `.env` file

   ```
   SUPABASE_URL=
   SUPABASE_KEY=
   ```

10. Run the local server

    ```
    # http://127.0.0.1:8000/
    # http://localhost:8000/
    # http://<public-ip>:8000/

    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```
11. (Optional) Paste the `seed.sql` file into Supabase's SQL editor (to seed the database)
    