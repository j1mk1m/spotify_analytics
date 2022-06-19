# Spotify Analytics Web Application

Author: James Gyeongwon Kim (j1mk1m)   
Description: This web application uses Oauth authentification to access the Spotify API, which allows users to connect to their Spotify accounts to display their account information, recently played tracks, playlists, and top artists and tracks. Furthermore, the python module allows user to create recommended playlists based on similar tracks, albums, artists, and keywords.

See the web application on your web browser: https://spotify-analytics-j1mk1m.herokuapp.com/

### How to run the project
**Set up your Spotify Developer account**
1. Create/Log into Spotify Developer account and navigate to the dashboard: https://developer.spotify.com/dashboard/login
2. Create a new application with name and description
3. Obtain the CLIENT_ID and CLIENT_SECRET from the dashboard page

**Set up the project**
1. Clone this git repository on your local machine.
2. Download the neccessary packages using the command "npm install"
3. Navigate to app.js file and update the following parameters
    1. *client_id* with your own client id
    2. *client_secret* with your own client secret
    3. *redirect_uri* with http://localhost:8888/callback (to run the server locally)
4. OR ALTERNATIVELY, 
    1. create an ".env" file 
    2. using the template ".env_sample", assign the variables with your own *client id* and *client secret*
    3. Go to app.js to change the *redirect_uri* to http://localhost:8888/callback (to run the server locally)
5. Go back to the Spotify dashboard and go to "edit settings"
  1. add *http://localhost:8888* and *http://localhost:8888/callback* to **Redirect URIs**

**Run the project**
1. Start the server by running "node app.js" on command-line
2. Open your browser and navigate to http://localhost:8888 to see web application
3. Click log in to sign in with your Spotify account
4. Authorize the app to use your Spotify information
5. You will then see the main page with your account information, recently played tracks, playlists, top artists, and top tracks.
6. Click Log out to log out of spotify (this will redirect you to the Spotify logout page)

### Credits
This project was adapted from the *Web API Tutorial* from Spotify: https://developer.spotify.com/documentation/web-api/quick-start/
