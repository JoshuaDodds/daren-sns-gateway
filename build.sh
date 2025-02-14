#!/usr/bin/env bash

# source some env vars that we dont want to put under version control
source .env || exit 1

# tell docker to switch to QEMU when reading other executable binaries
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes

echo "$CR_PAT" | docker login ghcr.io -u USERNAME --password-stdin
# homestack-utils
docker rmi ghcr.io/joshuadodds/daren-sns-gateway:latest
docker buildx build --platform linux/arm64 -t ghcr.io/joshuadodds/daren-sns-gateway:"$DSG_VERSION" -t ghcr.io/joshuadodds/daren-sns-gateway:latest -f Dockerfile --push .

# cleanup untagged
docker image prune -f
