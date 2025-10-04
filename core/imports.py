from twilio.rest import Client
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager
from flask_cors import CORS
from datetime import timedelta, datetime
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flasgger import Swagger
from datetime import datetime, timedelta, date
import random
import string
import os
from flask_bcrypt import Bcrypt
import threading
import time
from dotenv import load_dotenv
import filetype
import threading
import base64
import io
import numpy as np
from PIL import Image
import cv2
import json
from flask import Blueprint
import re
import cloudinary.uploader
from sqlalchemy.exc import IntegrityError
from flask_socketio import SocketIO, emit
import uuid