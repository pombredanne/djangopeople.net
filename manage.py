#!/usr/bin/env python
import os
import sys

import envdir


if __name__ == "__main__":
    if 'test' in sys.argv:
        env_dir = os.path.join('tests', 'env')
    else:
        env_dir = 'env'
    envdir.read(env_dir)

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
