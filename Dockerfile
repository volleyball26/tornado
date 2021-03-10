FROM hub.docker.com/layers/sunliren1997/public_docker:v1

#RUN pip uninstall pycurl
#RUN export PYCURL_SSL_LIBRARY=openssl
#RUN export LDFLAGS=-L/usr/local/opt/openssl/lib;export CPPFLAGS=-I/usr/local/opt/openssl/include;
#RUN pip install pycurl --compile --no-cache-dir
COPY requirements.txt /tmp/requirements.txt

RUN cd /tmp && pip install --no-cache-dir -r requirements.txt -i  https://pypi.doubanio.com/simple/  --trusted-host pypi.doubanio.com
