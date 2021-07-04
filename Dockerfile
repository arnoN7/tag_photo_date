FROM ubuntu:latest

RUN apt-get update \
  && apt-get install -y python3-pip python3-dev \
  && cd /usr/local/bin \
  && ln -s /usr/bin/python3 python \
  && pip3 install --upgrade pip
RUN apt install locales locales-all -y
RUN locale-gen en_US.UTF-8
RUN update-locale LANG=en_US.UTF-8
ENV TZ=Europe/Paris
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt install tzdata -y
RUN apt install openssh-server sudo bash-completion tree git -y

# set the working directory in the container
WORKDIR /code

# copy the dependencies file to the working directory
COPY requirements.txt .

# install dependencies
RUN pip install -r requirements.txt

# copy the content of the local src directory to the working directory
COPY src/ .
EXPOSE 5000
# command to run on container start
CMD [ "python", "./geotag_photos.py", "--server", "--tag", "/", "--gps", "/" ]