import docker
import os
import shutil
import uuid

from docker.errors import APIError
from docker.errors import ContainerError
from docker.errors import ImageNotFound

CURRENT_DIR = os.path.dirname(os.path.relpath(__file__))
IMAGE_NAME = 'ts755/ubuntu:oj-docker-updated'

client = docker.from_env()

TEMP_BUILD_DIR = "%s/tmp/" % CURRENT_DIR
CONTAINER_NAME = "%s:latest" % IMAGE_NAME

SOURCE_FILE_NAMES = {
	"java": "Example.java",
	"python": "example.py",
	"c++": "example.cpp"
}

BINARY_NAMES = {
	"java": "Example",
	"python": "example.py",
	"c++": "example"
}

BUILD_COMMANDS = {
	"java": "javac",
	"python": "python3",
	"c++": "g++"
}

EXECUTE_COMMANDS = {
	"java": "java",
	"python": "python3",
	"c++": "./"
}


def load_image():
	try:
		client.images.get(IMAGE_NAME)
		print("image exists locally")
	except ImageNotFound:
		print("Image not found locally, loading from docker hub")
		client.image.pull(IMAGE_NAME)
	except APIError:
		print("Can't connect to docker")

	return

def make_dir(dir):
	try:
		os.mkdir(dir)
	except OSError:
		print("Can't create directory")

def build_and_run(code, lang):
	result = {'build': None, 'run': None, 'error': None}

	source_file_parent_dir_name = uuid.uuid4()

	source_file_host_dir = "%s/%s" % (TEMP_BUILD_DIR, source_file_parent_dir_name)

	source_file_guest_dir = "/test/%s" % (source_file_parent_dir_name)

	make_dir(source_file_host_dir)
	print("source_file_dir is = %s/%s" %((source_file_host_dir), SOURCE_FILE_NAMES[lang]))

	if lang == 'java' or lang == 'python':
		cmd1 = "%s %s" % (BUILD_COMMANDS[lang], SOURCE_FILE_NAMES[lang])
		cmd2 = "%s %s" % (EXECUTE_COMMANDS[lang], BINARY_NAMES[lang])
	else:
		cmd1 = "%s -o %s %s" % (BUILD_COMMANDS[lang], BINARY_NAMES[lang], SOURCE_FILE_NAMES[lang])
		cmd2 = "%s%s" % (EXECUTE_COMMANDS[lang], BINARY_NAMES[lang])

	with open("%s/%s" % (source_file_host_dir, SOURCE_FILE_NAMES[lang]), 'w') as source_file:
		source_file.write(code)

	try:
		client.containers.run(
			image = IMAGE_NAME,
			command = cmd1,
			volumes = {source_file_host_dir: {'bind': source_file_guest_dir, 'mode': 'rw'}},
			working_dir = source_file_guest_dir
		)

		print("source built")

		result['build'] = 'OK'
	except ContainerError as e:
		result['build'] = str(e.stderr, 'utf-8')
		shutil.rmtree(source_file_host_dir)

		return result

	try:
		log = client.containers.run(
			image = IMAGE_NAME,
			command = cmd2,
			volumes = {source_file_host_dir: {'bind': source_file_guest_dir, 'mode': 'rw'}},
			working_dir = source_file_guest_dir
		)

		log = str(log, 'utf-8')

		print (log)

		result['run'] = log
	except ContainerError as e:
		result['run'] = str(e.stderr, 'utf-8')
		shutil.rmtree(source_file_host_dir)

		return result

	shutil.rmtree(source_file_host_dir)
	return result