#!/usr/bin/env bash

# Auto-increment versioning in .env
update_version() {
    ENV_FILE=".env"
    TODAY=$(date +"%Y.%-m.%-d")  # Remove leading zeros in month/day (e.g., 2025.2.16)

    # Extract current DSG_VERSION from .env
    if [ -f "$ENV_FILE" ]; then
        CURRENT_VERSION=$(grep -E "^DSG_VERSION=" "$ENV_FILE" | cut -d '=' -f2 | tr -d '"')
    else
        CURRENT_VERSION=""
    fi

    if [[ $CURRENT_VERSION =~ ^([0-9]{4})\.([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
        CUR_DATE="${BASH_REMATCH[1]}.${BASH_REMATCH[2]}.${BASH_REMATCH[3]}"
        PATCH_NUM="${BASH_REMATCH[4]}"

        if [[ "$CUR_DATE" == "$TODAY" ]]; then
            PATCH_NUM=$((PATCH_NUM + 1))  # Increment patch if it's the same day
        else
            PATCH_NUM=1  # Reset patch if it's a new day
        fi
    else
        PATCH_NUM=1  # Start fresh if no valid version found
    fi

    NEW_VERSION="${TODAY}.${PATCH_NUM}"

    # Update .env file
    if grep -q "^DSG_VERSION=" "$ENV_FILE"; then
        sed -i "s/^DSG_VERSION=.*/DSG_VERSION=\"$NEW_VERSION\"/" "$ENV_FILE"
    else
        echo "DSG_VERSION=\"$NEW_VERSION\"" >> "$ENV_FILE"
    fi

    export DSG_VERSION="$NEW_VERSION"
    echo "Updated DSG_VERSION to: $DSG_VERSION"
}

# Update version in .env before running the build
update_version

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
