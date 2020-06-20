import logging

import fire

# TODO(Rhys): move this elsewhere (ideally some kind of core library!)
root_logger = logging.getLogger('')

def log(message):
    root_logger.log(msg=message, level=logging.CRITICAL)


def generate_project(project_description_file_path, target_directory_path=None, expected_output_directory_path=None):
    # NOTE(Rhys): I'd build a docker image here with a mounted container so that we can compare what's generated in the container to what we have on the local machine
    # For now just generate in line

    # Generate project
    log(message=f'Generating {project_description_file_path}...')

    if expected_output_directory_path:
        log(message=f'Comparing to {expected_output_directory_path}...')
        # TODO(Rhys): run diff
        pass


if __name__ == "__main__":
    fire.Fire(generate_project)
