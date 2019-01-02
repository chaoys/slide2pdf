#!/usr/bin/env python

from flask import Flask, request, render_template, abort
from slide2pdf import valid_url, slide2pdf

app = Flask(__name__)

@app.route('/do', methods=['POST'])
def output():
	pdf = None
	url = request.form['slideurl']
	if valid_url(url):
		pdf = slide2pdf(url)
	else:
		abort(400)
	if pdf:
		link = '/{}'.format(pdf)
		return render_template('output.html', pdflink=link)
	else:
		return render_template('error.html')
