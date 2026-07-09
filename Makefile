.PHONY: docker-lint docker-build docker-run clean build run

docker-lint:
    docker run --rm -i hadolint/hadolint < Dockerfile

docker-build:
    docker buildx build -t warrentbot:latest .

docker-run: docker-build
    docker run -it --rm --env-file ./.env warrentbot:latest

clean:
    docker system prune -af --volumes
    docker builder prune -af

build: docker-build

run: docker-run
