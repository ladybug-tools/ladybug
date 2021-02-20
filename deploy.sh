#!/bin/sh

if [ -n "$1" ]
then
  NEXT_RELEASE_VERSION=$1
else
  echo "A release version must be supplied"
  exit 1
fi

CONTAINER_NAME="ladybugtools/ladybug"

echo "PyPi Deployment..."
echo "Building distribution"
python setup.py sdist bdist_wheel
echo "Pushing new version to PyPi"
twine upload dist/* -u $PYPI_USERNAME -p $PYPI_PASSWORD 


echo "Docker Deployment..."
echo "Login to Docker"
echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin

docker build . -t $CONTAINER_NAME:$NEXT_RELEASE_VERSION 
docker tag $CONTAINER_NAME:$NEXT_RELEASE_VERSION $CONTAINER_NAME:latest

docker push $CONTAINER_NAME:latest
docker push $CONTAINER_NAME:$NEXT_RELEASE_VERSION
