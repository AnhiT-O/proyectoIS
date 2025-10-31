#!/bin/bash

sudo systemctl stop gunicorn
sudo systemctl stop gunicorn_tauser
sudo systemctl stop nginx
echo "Servicios detenidos."