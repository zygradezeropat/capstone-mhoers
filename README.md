# MHOERS-RMS
" dont push the .venv so that you dont need to reinstall it "

" delete the venv and recreate new cause the path is not the same "

# code after deleting the .venv
- - python -m venv .venv - -
- - .venv/Scripts/Activate - - # make sure your in the right folder path
- - pip install -r requirements.txt - - # ensure install the needed libraries
- - cd MHOERS - - # to get inside the folder code
- - python manage.py runserver - - # to run the server and see the content of code

" recommended to install pgAdmin4 for GUI postgresql file "
" ill give the database sql later "