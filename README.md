# Scalable Multi-Room Chat App
## Heroku Flask-SocketIO Redis Eventlet Gunicorn
 
Check out this [project on heroku](https://smart-chat-room.herokuapp.com/).

![alt text](https://github.com/alexsmartens/simple-chat-room/blob/dev/ScreenShotChat.JPG)

### Running locally

1) Download/clone the project.
2) Navigate to the project directory.
3) Install all the dependencies from `requirements.txt`.
4) Launch the server with `gunicorn --worker-class eventlet -w 1 chat_server:app`.
5) Open `http://127.0.0.1:8000/` in your favourite browser and start chatting.

### Deploying on Heroku with Git
Refer to [deploying with Git](https://devcenter.heroku.com/articles/git).
