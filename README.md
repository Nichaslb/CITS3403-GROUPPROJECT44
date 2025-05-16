# CITS3403

**League of Stats** is a statistics and analysis hub for the game League of Legends designed to give players deeper insights into their performance in the game. The application combines account data, player performance statistics, champion information, and user-created guides to provide an all-in-one experience for casual and competitive players alike.

### Users can:

- Sign up and log in, where upon signing up the account will link to the player's account in the official game.

- Create guides, with customizable visibility and access settings.

- Edit and publish these guides for others to view and learn from.

- View and compare player accounts to analyze gameplay and performance.

- Explore detailed information on champions and lore, enhancing both strategic understanding and immersion in the League of Legends universe.


Contributors to this project are as follows:

-
|   Student number  | Full name  | Github   |
|   :---:  | :---:           | :---:        |
| 23852114 | Mandy Song	     | mandysong96 |
| 24314307 | Nicolas Hasleby | Nichaslb     |
| 23740463 | Alicia Suann    | clarebearuwa  |
| 24205379 | Alex Zhao       | Choukaretsu  |


File structure

- `migrations/` - **Database Migrations** Stores migration scripts to track changes in the database schema (like creating or modifying tables).
  - `routes/` - **Route Handlers** Stores route logic organized into modular files using Flask Blueprints.
  - `static/` - **Static Files** Consists of Images (.jpg, .png), CSS files (.css), and JavaScript (.js) folders referenced in HTML files.
  - `templates/` -  **HTML Templates** Stores all Jinja2 HTML templates.

  - `.gitignore` - **Ignore Github Rules** Lists files/folders Git should not track.
  - `README.md` - **Project Overview** Markdown file describing the overview of the project.
  - `app.py` - **Main Application File** Entry point of the app, containing Flask app initialization, blueprint registration, configuration, app run command.
  - `forms.py` - **Form Classes** Form definitions with Flask-WTF
  - `models.py` - **Database Models** Contains SQLAlchemy model classes that map to database tables.
  - `requirements.txt` - **Python Dependencies** List of all required Python packages for the project, installed with pip install -r requirements.txt (bash).


### Prerequisites

- Python 3.x installed
- Flask framework

### Instllation

The following will show you the steps to run the application.

1. **Open a Command Prompt/ Terminal**
*Open Command Prompt for Windows by pressing the keys Win + R, typing cmd annd clicking 'OK',or on Terminal for macOS/Linux by opening the Terminal app.*

2. **Clone the repository**
*Use the repository link to clone it to your local machine, then navigate to the project directory.*
```bash
git clone https://github.com/yourusername/CITS3403.git
cd CITS3403
```

3. **Set up a Virtural Environment**
*Then, activate it*
```bash
python -m venv venv
```
*Windows*
```bash
venv\Scripts\activate
```
*macOS/Linux*
```bash
source venv/bin/activate
```

4. **Install dependencies:**
```bash
pip install -r requirements.txt
```

5. **Run the application**
```bash
flask run
```

6. **Open your browser and navigate to the website listed**



### Testing


**Running Tests**

Use the following command to run all unit test and selenium tests:
```bash
python -m unittest discover -s tests
```

To run a specific test file:
```bash
python -m unittest tests.test_app
```

**Exiting app**

*To deactivate the virtual environment when you're done, simply type:*
```bash
deactivate
```

### References


**Disclaimer**
League of Stats is not affiliated with RiotGames.
League of Legends, game content and materials are trademarks and copyrights of RiotGames.
This website and all associated visual content are not affiliated with or endorsed by Riot Games. All intellectual property belongs to Riot Games

*League of Legends Character Renders and Icons*
Source: Riot Games - Official Media
Attribution: © Riot Games. All character artwork, renders, and icons are the property of Riot Games and are used here for non-commercial, educational purposes only.
Accessed via: In-game assets, League Wiki (https://leagueoflegends.fandom.com)

*Splash Arts / Background Images*
Source: League of Legends Fandom Wiki
Attribution: All splash arts and champion backgrounds are © Riot Games and are provided through community-contributed assets hosted on the League Wiki.
Use: For visualization in an academic/web development project (CITS3403)

*Welcome Page Wallpaper*
Title: League of Legends wallpaper used in GDC 2015 coverage
Source: SiliconANGELOriginal URL: https://siliconangle.com/2015/03/03/league-of-legends-dev-talks-balancing-depth-with-fun-gdc2015/league-of-legends-wallpaper/
Attribution: © Riot Games — image used in an article for illustrative/reporting purposes. Included in this project under fair use for academic submission.
Use: The first screen upon entering the web application, as the Welcome Page

*Stat Icons (HP, AD, MR, etc.)*
Source: Riot Games’ in-game UI assets and League Wiki icon pages
Attribution: Icons are property of Riot Games. Accessed for educational UI representation only.
