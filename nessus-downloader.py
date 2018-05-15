import requests
import json
import sys
import time


# Disable Warning when not verifying SSL certs.
requests.packages.urllib3.disable_warnings()


url = 'https://url:8834' # change url with your nessus url
verify = False
token = ''
username = 'foo' # change this with your actual username
password = 'bar' # change this with your actual password
nessus = 'nessus'


def build_url(resource):
	return '{0}{1}'.format(url, resource)


def connect(method, resource, data=None, params=None):
	"""
	Send a request

	Send a request to Nessus based on the specified data. If the session token
	is available add it to the request. Specify the content type as JSON and
	convert the data to JSON format.
	"""
	headers = {'X-Cookie': 'token={0}'.format(token),
			   'content-type': 'application/json'}

	data = json.dumps(data)

	if method == 'POST':
		r = requests.post(build_url(resource), data=data, headers=headers, verify=verify)
	elif method == 'PUT':
		r = requests.put(build_url(resource), data=data, headers=headers, verify=verify)
	elif method == 'DELETE':
		r = requests.delete(build_url(resource), data=data, headers=headers, verify=verify)
	elif method == 'GET':
		r = requests.get(build_url(resource), params=params, headers=headers, verify=verify)
	else:
		print(Error)
	# Exit if there is an error.
	if r.status_code != 200:
		e = r.json()
		#e= json.load(r)
		print e['error']
		sys.exit()

	# When downloading a scan we need the raw contents not the JSON data. 
	if 'download' in resource:
		return r.content
	
	# All other responses should be JSON data. Return raw content if they are
	# not.
	try:
		return r.json()
	except ValueError:
		return r.content


def login(usr, pwd):
	"""
	Login to nessus.
	"""

	login = {'username': usr, 'password': pwd}
	data = connect('POST', '/session', data=login)

	return data['token']

def getScanInfoById(_id):
	"""
	Get Info of scan selected by its ID
	"""

	data = connect('GET', ('/scans/%d' % (_id)))

	return data

def getScans():
	"""
	Get scans From Nessus
	"""
	data = connect('GET','/scans')
	return data


def getScansIds(scans, i):
	"""
	returns scan ID
	"""

	return scans['scans'][i]['id']


def getScansHistoryIds(scan_info):
	"""
	return the last history ID (last modification )of a scan selected by its ID
	"""

	if scan_info['history'] != None:
		return scan_info['history'][-1]['history_id']
	else:
		pass

def getScansName(scans, i):
	"""
	returns the name of a scan
	"""

	return (scans['scans'][i]['name'])


def GetScanResultByHistoryId(_id, _hist_id):
	"""
	returns the file's identifier (the scan result of a specific scan selected by the id and history_id)
	"""

	data_post = {'format': nessus}
	data = connect('POST', ("/scans/%d/export?history_id=%d" % (_id, _hist_id)), data=data_post)

	return data['file']


def check_status(_id, _file_id):
	"""
	Checks the status of a scan [Loading, Ready]
	"""

	data = connect('GET', ('/scans/%d/export/%d/status' % (_id, _file_id)))

	return data['status']

def DownloadReport(_id, _file_id):
	"""
	Downloading report
	"""

	data = connect('GET', ('/scans/%d/export/%d/download' % (_id, _file_id)))

	return data

def writeToFile(_data, _file_name):
	"""
	Write the Downloaded scan to a file
	"""

	file_name = _file_name+'.nessus'

	try:
		with open(file_name, 'w') as the_file:
			the_file.write(_data)
		the_file.close()
	except IOError:
		print('File error')


def logout():
	"""
	Logout of nessus.
	"""

	connect('DELETE', '/session')

if __name__ == '__main__':
	print('Login')
	token = login(username, password)
	#print('Token: {0}'.format(token))
	scans = getScans()

	i = 0
	#_not_ready = {}
	while i < len(scans['scans']):

		_id = getScansIds(scans,i)
		_file_name = getScansName(scans,i)
		if _file_name not in ["AP Scans ", "NE ","SE", "SE Scans"]:
			_hist_id = getScansHistoryIds(getScanInfoById(getScansIds(scans,i)))
			
			if _hist_id != None:
				_file_id = GetScanResultByHistoryId(_id, _hist_id)
				print('sleeping for 15 seconds')
				time.sleep(15)
				res = check_status(_id, _file_id)
				if res == 'ready':
					print('ready !!')
					print('Downloading Scan : {} ...!!'.format(_file_name))
					writeToFile(str(DownloadReport(_id, _file_id)), _file_name)
					#print(DownloadReport(_id, _file_id))
					print('donwload finished!!')
				else:
					print('Scan {} is still loading!!!'.format(_file_name))
					print('sleeping for 15 seconds')
					time.sleep(15)
					res = check_status(_id, _file_id)
					if res == 'ready':
						print('ready !!')
						print('Downloading Scan : {} ...!!'.format(_file_name))
						writeToFile(str(DownloadReport(_id, _file_id)), _file_name)
						#print(DownloadReport(_id, _file_id))
						print('donwload finished!!')
					else:
						print('Scan {} is still loading!!!'.format(_file_name))
						
			else:
				i = i+1
				continue
		i = i+1
	print('All Ready Scan Were Downloaded')
  
	print('Logout')
	logout()
