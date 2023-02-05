#!/bin/bash
protoc -I=../proto/ --python_out=../minetests/proto --cpp_out=../src ../proto/*.proto
