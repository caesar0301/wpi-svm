pr-svm
======

To reconstruct web page from network traffic using support vector machine.


"logbaic.py"
Supporting basic fuctions of log procession.

New Format:
plain text
one line for one web request/response
time	dns	connect	send	wait	receive	flow-id	user-agent-id	sourceip	sourceport	destip	destport	request-version	response-version	request-method	response-status	request-header-size	request-body-size	response-header-size	response-body-size	response-content-type	url referrer	redirect-url
Seperator between items is '\t\t'. Lost item is replaced by 'N/A'
