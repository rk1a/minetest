#!/bin/bash
protoc -I=../proto/ --python_out=proto_python/ --cpp_out=../src ../proto/*.proto
