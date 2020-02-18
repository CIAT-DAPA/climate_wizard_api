FROM debian:buster-slim

MAINTAINER Steven Sotelo <stevenbetancurt@hotmail.com>

ENV WOCAT_APP=/var/www/html/ \
    APACHE_CONF=/etc/apache2/sites-available/000-default.conf \
    WOCAT_REQUIREMENTS=/tmp/requirements.txt

RUN apt-get update \
    && apt-get install -y --no-install-recommends \	
        build-essential \	
        ssl-cert \
        libapache2-mod-wsgi \
        apache2 \
        apache2-utils \        
        python \
        python-dev \
        python-pip \
        libgdal-dev \
        python-gdal \
        vim \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip \
    && pip install --upgrade setuptools \    
    && rm /var/www/html/index.html 
    
COPY ./app.wsgi ${WOCAT_APP}
COPY ./bottle.py ${WOCAT_APP}
COPY ./service.py ${WOCAT_APP}
COPY ./000-default.conf ${APACHE_CONF}
COPY ./requirements.txt ${WOCAT_REQUIREMENTS}

RUN pip install -r ${WOCAT_REQUIREMENTS} \
    && rm ${WOCAT_REQUIREMENTS}

VOLUME [ "/mnt" ]

EXPOSE 80

CMD ["/usr/sbin/apachectl", "-D", "FOREGROUND"]

# docker build -t stevensotelo/climatewizard:latest .

# docker run -p 8086:80 --name wocat -d stevensotelo/climatewizard:latest
# docker exec -it wocat bash