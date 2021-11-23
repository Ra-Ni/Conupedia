# shellcheck disable=SC2164
cd src
uvicorn application:app --workers 10 --host "0.0.0.0" --port 80