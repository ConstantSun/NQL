FROM --platform=linux/amd64 python:3.8-slim-buster

WORKDIR /python-docker

COPY . .
RUN chmod 775 setup.sh
RUN /python-docker/setup.sh

EXPOSE 8080

CMD [ "python", "-m" , "flask", "run", "--host=0.0.0.0", "--port=8080"]