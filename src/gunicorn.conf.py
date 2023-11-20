wsgi_app = "camtrap:server"

bind = "0.0.0.0:9002"

# logging
accesslog = "/var/log/camtrap/access.log"
errorlog = "/var/log/camtrap/error.log"

# daemon = True
user = None
group = None

workers = 1
backlog = 64
