.PHONY: docker-lint docker-build docker-run clean build run

docker-lint:
    docker run --rm -i hadolint/hadolint < Dockerfile

docker-build:
    docker buildx build -t warrenbot:latest .

docker-run: docker-build
    docker run -it --rm --env-file ./.env warrenbot:latest

clean:
    docker system prune -af --volumes
    docker builder prune -af

build: docker-build

run: docker-run
