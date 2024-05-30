## Requirements
This project requires python and pip(https://pypi.org/project/pip/), and SQLite3 which has been in the standard python library since ver 2.5.
Note that installing FastAPI using pip should normally install the others below it by default\
    -pip install fastapi\
    -pip install uvicorn\
    -pip install jinja2\
    -pip install python-multipart

## Usage
    - Navigate to the location of main.py 
    - $ uvicorn main:app
    - App will run at localhost:8000 in the browser by default
    - Log in with different user accesslevels :
    username:admin and pw:123,
    or username:user and pw:123
You can rename default_bughound.db to bughound.db to use the database with just the two initial users.


## About
This web app is constructed using the FastAPI framework on the backend, which uses python to create fast web apps.
It uses SQLite3 which is a fast ORM SQL database held on the drive
For the frontend it uses some html, jquery and bootstrap components.