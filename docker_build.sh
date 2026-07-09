#set -o pipefail

docker build -t myapp . | tee build.log

echo "Build successful"