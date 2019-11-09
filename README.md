# KOWHOWSE

**KOWHOWSE** is a listening test creation tool built in Django. Using this tool, you can create a listening test with potentially several different types of questions (AB, ABX and MOS currently supported) with a short Python script.

## Getting Started
Clone the repository to your local machine:
```
git clone git@github.com:KurtAhn/KOWHOWSE.git
```

Then, set up an SQL database where your survey definitions, user responses, etc. will be stored:
```
cd path/to/KOWHOWSE
python web/manage.py migrate
```

You will also need to create a superuser account, so that you can grant yourself access to the database:
```
python web/manage.py createsuperuser
```

To create a survey, write a Python script with a `survey_definition` function, where you define the structure of your survey. Example scripts can be found in `examples/`.

Once you have your survey definition script, put the survey definition on the database:
```
python web/manage.py --pythonpath web/kowhowse createsurvey path/to/survey_definition.py
```

To share your survey with testers, run a server for the **KOWHOWSE** app to go online:
```
python web/manage.py runserver [<port>]
```

Once the server is running, using your superuser credentials, you can access the *Backroom*, where you can perform administrative actions. Here, you will be able to find the link to your survey, which you can provide to your testers.