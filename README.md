# Mastermind
### Tool for naive local deploy.
What is solves? You have host where you want to have your applications deployed
for developing/testing/showing. So, for example, you can send build request inside
pipeline to Mastermind. It will clone your repository, execute build and start commands
(specified by you in request), create reverse proxy from hostname(specified by you)
 to your deployed application.

**WARNING: In current version build and start commands are executed in host OS directly**

## TODO:
 - build rotation
 - branch selection
 - dockerization for security purposes
 - your proposals?


## pre-requisites
 - python3.8
 - caddy webserver
 - git
 - postgres

## API
```sh
pip install -r requirements.txt
docker-compose up -d db
caddy start
uvicorn api:app
```

## Builder (bladerunner)
It looks for pending build task and performing it. Should work as daemon.
```sh
python bladerunner.py
```

## Watcher (beholder)
This part checks pulse of launched applications and keeps theirs status actual
```sh
python beholder.py
```

## How to queue your build
Send http POST request to Mastermind`s awaken API, example:
```
{
  "reverse_proxy_from": "test.local",
  "repository": "git@github.com:hanxi/http-file-server.git",
  "up_command": "python2 file-server.py ./ %PORT%",
  "build_command": "echo build passed"
}
```
Do not forget to add reverse proxy hostname to you hosts file
