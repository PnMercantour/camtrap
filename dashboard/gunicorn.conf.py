wsgi_app='camtrap:server'

#logging
accesslog = 'log/access.log'
errorlog = 'log/error.log'

#daemon = True
user=None
group=None

workers = 1
backlog=64
bind = 'unix:apache2.sock'



