#!/bin/bash

mkdir -p build
mkdir -p layers

package_lambda () {
  service=$1
  name=$2
  echo "Packaging $name"
  rm -rf temp
  mkdir -p temp/python
  pip install -r "$service/requirements.txt" -t temp/python
  cd temp
  zip -r ../layers/"${name}"-layer.zip python
  cd ..
  rm -rf temp/python
  cp "$service/app.py" temp/
  cd temp
  zip -r ../build/"${name}".zip .
  cd ..
  rm -rf temp
}

for service in services/*; do
  name=$(basename "$service")
  package_lambda "$service" "$name"
done

for auth in auth/*; do
  name=$(basename "$auth")
  package_lambda "$auth" "$name"
done

for cron in cron/*; do
  name=$(basename "$cron")
  package_lambda "$cron" "$name"
done
