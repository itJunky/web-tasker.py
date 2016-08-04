# web-tasker.py

## Simple task treker for web on flask framework

![alt tag](https://raw.githubusercontent.com/itJunky/web-tasker.py/master/current_screenshot/web-tasker-py-0-1.png)

You can try it on my hosting here http://tasker.itjunky.ws

For run on development environment you need a docker
Than you need to go into web-tasker.py directory and run docker-compose up

If it's your first run, you need to edit init.sh for uncomment a line

```python ./db_create.py```

And comment out line

```python ./runserver.py```

After that you need run docker-compose up

Than change back init.sh with uncomment line

```python ./runserver.py```

And comment line with db_create
After that run again docker-compose up
