wpi-svm
======

A tool to generate features (as input to `libsvm`) to identify web page from network traffic with Support Vector Machine. 

Dependencies
---------------

[pyTree] (https://github.com/caesar0301/pyTree): python module implementing tree data structure. 
This module must be put into `lib` folder to be quoted correctly.

[libsvm](http://www.csie.ntu.edu.tw/~cjlin/libsvm/): A Library for Support Vector Machines

Main Programs
---------------

`FGen_log.py`: generate features from logs

`FGen_har.py`: generate features from [HAR](http://www.softwareishard.com/blog/har-12-spec/) files

`har2log.py`: convert HAR files into HTTP logs with format below

HTTP Logs
--------------

* Log file is generate by another project [http-sniffer](https://github.com/caesar0301/http-sniffer), which sniffers raw network traffic (trace files) and extracts HTTP logs.

* If there isn't raw network trace on hand and only HAR format files (exported by like firebug), you can convert these HAR files into logs using `har2log.py`; but this method is just for validation. We also provide a tool `FGen_har.py` to generate features directly from HAR files without convertion.

* Log format

Plain text, each line records a web page element. Lost item is replaced by 'N/A'.

    [time]\t\t[dns]\t\t[connect]\t\t[send]\t\t[wait]\t\t[receive]\t\t[flow-id]\t\t[user-agent-id]\t\t[sourceip]\t\t[sourceport]\t\t[destip]\t\t[destport]\t\t[request-version]\t\t[response-version]\t\t[request-method]\t\t[response-status]\t\t[request-header-size]\t\t[request-body-size]\t\t[response-header-size]\t\t[response-body-size]\t\t[response-content-type]\t\t[url]\t\t[referrer]\t\t[redirect-url]

Tools Folder
---------------

A collection of tools to analysis data for research paper.