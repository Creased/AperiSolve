#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""
Aperi'Solve - Flask application
Aperi'Solve is a web steganography plateform.

__author__ = "@Zeecka"
__copyright__ = "WTFPL"

"""

import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from appfunct import *
import stega

app = Flask(__name__)

APP_PORT = int(os.getenv('APP_PORT', 80))
APP_RM_FILE_TIME = int(os.getenv('APP_RM_FILE_TIME', 10))  # Keep images for N minutes maximum
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('APP_MAX_SIZE', 16 * 1024 * 1024))  # 16 Mega per image maxi
# Supported image types
imgExts = ["jpeg", "png", "bmp", "gif", "tiff", "jpg", "jfif", "jpe", "tif"]

@app.route('/')
def main():
    """ Upload Page """
    return render_template('index.html')


@app.errorhandler(Exception)
def error_handler(e):
    """ Error handler, mostly for wrong file """
    if "cannot identify" in str(e):  # Unknow image format
        # cannot identify image file 'uploads/xxx.jpg'
        a, *filename, b = str(e).split("'")  # Recover filename
        filename = ''.join(filename)
        os.remove(filename)  # Remove invalid file
        return jsonify({"Error": "Unknow file format."})
    return jsonify({"Error": str(e)})


@app.route('/upload', methods=['POST'])
def uploadImage():
    """ Upload image on server
    @fileup: Uploaded image (file)
    ---
    Return JSON array with:
    File: New file name on server
    Error: Error if upload fail
    """

    if "fileup" in request.files:
        f = request.files["fileup"]  # uploaded file
        ext = getExt(f.filename)

        if ext not in imgExts:
            return jsonify({"Error": "Invalid extension: "+str(ext)})

        newfilename = f.filename #randString()+"."+ext
        newpathfile = f"uploads/{newfilename}"
        f.save(newpathfile)  # Save file with new name

        return jsonify({"File": newfilename})

    return jsonify({"Error": "No file submitted."})


@app.route('/process', methods=['POST'])
def process():
    """ Process layers decomposition
    @filename : Uploaded image (filename)
    ---
    Return JSON array with:
    Images : n * 8 images (path)
    Error: Error if file doesnt exist
    """
    if "filename" in request.form:
        f = request.form["filename"]  # already uploaded file
        pathfile = f"uploads/{f}"

        if not os.path.isfile(pathfile):
            return jsonify({"Error": "File doesn't exist."})

        images = stega.processImage(f, "uploads/")  # Generate Images

        return jsonify({"Images": images})
    return jsonify({"Error": "No filename submitted."})


@app.route('/zsteg', methods=['POST'])
def zsteg():
    """ Process zsteg analysis.
    @filename : Uploaded image (filename)
    @allzsteg : -a option for zsteg (bool)
    @zstegfiles : extract option for zsteg (bool)
    Return JSON array with:
    Zsteg : zsteg output
    Error: Error if file doesnt exist
    """
    if "filename" in request.form:
        f = request.form["filename"]  # already uploaded file
        pathfile = f"uploads/{f}"

        if not os.path.isfile(pathfile):
            return jsonify({"Error": "File doesn't exist."})

        allzsteg, zstegfiles = False, False
        if "allzsteg" in request.form:
            allzsteg = bool(int(request.form["allzsteg"]))
        if "zstegfiles" in request.form:
            zstegfiles = bool(int(request.form["zstegfiles"]))

        zstegoutput = stega.processZsteg(f, "uploads/", allzsteg,
                                         zstegfiles)

        return jsonify({"Zsteg": zstegoutput})
    return jsonify({"Error": "No filename submitted."})


@app.route('/binwalk', methods=['POST'])
def binwalk():
    """ Process binwalk analysis.
    @filename : Uploaded image (filename)
    Return JSON array with:
    Binwalk : binwalk output
    Error: Error if file doesnt exist
    """
    if "filename" in request.form:
        f = request.form["filename"]  # already uploaded file
        pathfile = f"uploads/{f}"

        if not os.path.isfile(pathfile):
            return jsonify({"Error": "File doesn't exist."})

        binwalkoutput = stega.processBinwalk(f, "uploads/")

        return jsonify({"Binwalk": binwalkoutput})
    return jsonify({"Error": "No filename submitted."})


@app.route('/steghide', methods=['POST'])
def steghide():
    """ Process steghide analysis.
    @filename : Uploaded image (filename)
    @passwdsteghide : Steghide passwd
    Return JSON array with:
    Steghide : Steghide output
    Error: Error if file doesnt exist / password is wrong
    """
    if "filename" in request.form:
        f = request.form["filename"]  # already uploaded file
        pathfile = f"uploads/{f}"

        if not os.path.isfile(pathfile):
            return jsonify({"Error": "File doesn't exist."})

        if len(request.form["passwdsteghide"]):
            steghideoutput = stega.processSteghide(
                f, "uploads/", request.form["passwdsteghide"])
        else:
            steghideoutput = {"Error":
                              "Steghide doesn't work without password."}

        return jsonify({"Steghide": steghideoutput})
    return jsonify({"Error": "No filename submitted."})


@app.route('/exiftool', methods=['POST'])
def exiftool():
    """ Process exiftools analysis.
    @filename : Uploaded image (filename)
    Return JSON array with:
    Exiftool : Exiftool output
    Error: Error if file doesnt exist
    """
    if "filename" in request.form:
        f = request.form["filename"]  # already uploaded file
        pathfile = f"uploads/{f}"

        if not os.path.isfile(pathfile):
            return jsonify({"Error": "File doesn't exist."})

        exiftooloutput = stega.processExif(f, "uploads/")

        return jsonify({"Exiftool": exiftooloutput})
    return jsonify({"Error": "No filename submitted."})


@app.route('/strings', methods=['POST'])
def strings():
    """ Process strings analysis.
    @filename : Uploaded image (filename)
    Return JSON array with:
    Strings : Strings output
    Error: Error if file doesnt exist
    """
    if "filename" in request.form:
        f = request.form["filename"]  # already uploaded file
        pathfile = f"uploads/{f}"

        if not os.path.isfile(pathfile):
            return jsonify({"Error": "File doesn't exist."})

        stringsimg = stega.processStrings(f, "uploads/")

        return jsonify({"Strings": stringsimg})
    return jsonify({"Error": "No filename submitted."})


@app.route('/uploads/<path>')
def uploads(path):
    """ Route for uploaded/computed files
    Remove old uploaded/computed files on each requests
    """

    # First remove old files
    cmdline(f"find uploads/ -mmin +{APP_RM_FILE_TIME} " +
             "-type f -exec rm -fv {} \;")
    return send_from_directory('uploads', path)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=APP_PORT)

