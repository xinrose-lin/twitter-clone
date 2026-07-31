## web server gateway interface - entry point for app 
## liek a run.py but for prod ?

from app import create_app 

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
