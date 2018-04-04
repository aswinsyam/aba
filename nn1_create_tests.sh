#!/bin/bash
set -e
# args[1:-1]: pcap files, arg[-1]: n_features

cd ..
JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64/
for file in ${@:1:${#}-1}; do
	cd dist/bin
	./CICFlowMeter "$file" ../../csv/test/extracted/
	cd ../..
done
[[ -d "csv/test/${@: -1}features/" ]] || mkdir "csv/test/${@: -1}features/"
python scripts/compact_flows.py csv/test/extracted/*.csv "csv/test/${@: -1}features/" -f "scripts/features/${@: -1}.txt"

