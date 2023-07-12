all: 

deps:
	#Install dependencies
	util/minetester/install_deps.sh
repos:
	#Init all submodules
	git submodule update --init --recursive


package: deps repos


