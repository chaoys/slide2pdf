#!/usr/bin/env python

import os
import re
import sys
import errno
import socket
import shutil
import urllib
import logging
import tempfile
from urlparse import urlsplit
import lxml
import requests
from bs4 import BeautifulSoup
from PIL import Image
from fpdf import FPDF

base_dir = '/tmp'
tmp_dir = base_dir + '/slides'
pdf_dir = base_dir + '/pdf'
log_file = base_dir + '/slide2pdf.log'

logging.basicConfig(filename=log_file, level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(message)s', datefmt='%Y-%m-%d %H:%M:%S')

def getslides(url, output_dir=None):
	socket.setdefaulttimeout(20)
	# grab slideshare html
	html = ''
	images = None
	try:
	    html = requests.get(url)
	    html.raise_for_status()
	except Exception, e:
	    logging.error('Could not download {}. {}'.format(url, e))
	    return None, None
	else:
	    # read html and get images
	    soup = BeautifulSoup(html.text, 'lxml')
	    images = soup.find_all('img', attrs={'class': 'slide_image'})

	# check if full resolution available
	if images[0].has_attr('data-full'):
	    # use full resolution
	    slide_resolution = 'data-full'
	elif images[0].has_attr('data-normal'):
	    # else use normal
	    slide_resolution = 'data-normal'
	else:
	    logging.error('Could not find slides.')
	    return None, None

	# download slides to tmp directory
	if output_dir is None:
		output_dir = tempfile.mkdtemp(dir=tmp_dir)
	downloaded_slides = []
	for i, image in enumerate(images, start=1):
	    # form slides data
	    remote_slide = image[slide_resolution]
	    local_slide = os.path.join(output_dir, 'slide-{}.jpg'.format(str(i)))

	    try:
		urllib.urlretrieve(remote_slide, filename=local_slide)
	    except Exception, e:
		logging.error('Could not download slide-{}. {}'.format(str(i), e))
		return None, output_dir
	    else:
		# add to array
		downloaded_slides.append(local_slide)

	return downloaded_slides, output_dir

def img2pdf(images, pdffile):
	try:
		p1 = Image.open(images[0])
	except Exception, e:
		logging.error('Image.open({}) failed'.format(images[0]))
		return None
	w, h = p1.size
	# 1 inch == 96 pixel
	hin = h/96 + 1
	win = hin*w/h + 1
	try:
		pdf = FPDF('P', 'in', (win, hin))
		pdf.add_page()
		pdf.set_font('courier', 'B', 30)
		pdf.cell(0, 3, 'slide2pdf.net', 0, 1, align='C', link='http://slide2pdf.net')

		for one in images:
			pdf.image(one, h=hin)
		pdf.output(pdffile)
	except Exception, e:
		return None
	
	return 'OK'

def valid_url(url):
	if url is None or url == '':
		return False
	url_tuple = urlsplit(url)
	if url_tuple.netloc != 'www.slideshare.net' and url_tuple.netloc != 'slideshare.net':
		logging.error('bad url "{}"'.format(url))
		return False
	return True

# url should be validated by valid_url before this
def slide2pdf(url):
	# build output file name from url
	urlMatch = re.search('(?:[^\/]*\/){3}([A-Za-z0-9-_\.]*)(?:\/)([A-Za-z0-9-_\.]*)', url)
	output_file =  '{}-by-{}.pdf'.format(urlMatch.group(2), urlMatch.group(1))
	pdf = os.path.join(pdf_dir, output_file)
	
	# fast path
	if os.path.isfile(pdf):
		return output_file
	
	slides, slides_dir = getslides(url)
	if slides is None:
		if slides_dir is not None:
			shutil.rmtree(slides_dir)
		return None
	
	if not os.path.isdir(pdf_dir):
		logging.error('The pdf output directory "{}" not found'.format(pdf_dir))
		return None
	
	if img2pdf(slides, pdf) is None:
		if os.path.isfile(pdf):
			os.remove(pdf)
		output_file = None
	shutil.rmtree(slides_dir)
	
	return output_file

