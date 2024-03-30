# Weather Recommendations
I noticed that my music taste tracks very closely with the current weather - so I made an app than understands that.\
You can check it out [here](https://weather-recommendations.onrender.com/). You can also view the endpoints at `/docs` route.
## Build from source
### Connecting with Spotify
You need to create a new app in the [Spotify developer dashboard](https://developer.spotify.com/dashboard) and add your development server address (e.g. http://127.0.0.1:8000/) to Redirect URIs column. This will also generate your apps Client ID and Client secret.
> [!IMPORTANT]
> Make sure that the address you added as Redirect URI in Spotify matches your dev server's address - including the trailing `/`
### Connecting with Weather API
I used [weather api](https://www.weatherapi.com/). After creating an account the key will be available in the Dashboard section.
### Dotenv
Create a .env file in the root of the project and fill it with previously generated API keys like so:
```
SPOTIFY_CLIENT_ID = <your spotify client id>
SPOTIFY_CLIENT_SECRET = <your spotify secret>
WEATHER_API_KEY = <your weather api key>
```
### Building
For development purposes I recommend using a virtual environment, so first create and run it using:
```
python3 -m venv env
source env/bin/activate
```
Then build the project using the following commands:
```bash
cd client
npm install
npm run build
cd ..
pip install -r requirements.txt
```
### Running
To run a development server:
```bash
uvicorn main:app --reload
```
> [!NOTE]
> If you make changes to the client code you'll need to rebuild it manually using `npm run build` in the client directory
