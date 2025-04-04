## Notes
Angular framework and tools are used as the frontend, using the Angular CLI, it is built, and then served statically by the FastAPI backend. There might be some conflicts/issues for the time being
Otherwise, from the root directory, use 'ng serve' to begin serving the angular pages, and 'uvicorn main:app' to run the server/backend, which might them on separate ports. But it works, though not pretty.
Call angular build and dependency downloads by the following, then serve:
  'npm install'

## Requirements
(note that on windows, you'll have to prefix with 'py -m' before using python modules)
- pip install -r requirements

Above should be all that is needed. Major requirements for installation are Python and pip(https://pypi.org/project/pip/), and SQLite3 which has been in the standard python library since ver 2.5.
Note that installing FastAPI using pip should normally install the others below it by default. You can install major components separately as below if needed.
 - pip install fastapi
 - pip install uvicorn
 - pip install jinja2
 - pip install python-multipart

## Usage
    - Navigate to the location of main.py 
    - $ uvicorn main:app
    - App will run at localhost:8000 in the browser by default
Log in with different user access levels(Admin can add and delete users,registered programs, and a few other Maintenance/Administration options):
- Username: admin and Password: 123,
- Username: user and Password: 123


## About
This web app is constructed using the FastAPI framework on the backend, which uses python to create fast web apps.
It uses SQLite3 which is a fast ORM SQL database held on the drive.
For the frontend it uses some html, jquery and Bootstrap components.
